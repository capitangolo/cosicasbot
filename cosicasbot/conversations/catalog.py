#!/usr/bin/env python
# -*- coding: utf-8 -*-

from ..filters import *
from . import start, cart
from math import ceil
from ..model.context import Conversation
from ..model.entities import *

__name__ = 'Catalog'

def _commands():
    return [
        catalogs,
        browse_catalog
    ]


def catalogs_conversation():
    return Conversation(), catalogs


def _end_catalogs(model, ctxt, chat, args):
    ctxt.conversations.end(model, ctxt, chat, args)


def _menu_catalogs(t, ctxt, catalogs):
    options = []
    params = []

    for catalog in catalogs:
        options.append( [[catalog.name, browse_catalog]] )
        params.append( [str(catalog.id)] )

    options.append( [[t.action_back, _end_catalogs]] )
    params.append( [] )
    return options, params


def _menu_products(t, products, page, page_count):
    options = []
    params = []

    if page > 0:
        options.append( [[ '⏪', _update_catalog_page ]] )
        params.append( [str( page - 1)] )

    for product in products:
        # TODO: Localize the price format
        title = "{} {:.02f}€".format(product.name, product.price)
        options.append( [[title, browse_product]] )
        params.append( [str(product.id), str(product.model), str('False')] )

    if page < page_count - 1:
        options.append( [[ '⏩', _update_catalog_page ]] )
        params.append( [str( page + 1)] )


    options.append( [[t.action_back, catalogs]] )
    params.append( [] )
    return options, params


def _menu_product(t, product, images, cctxt):
    options = []
    params = []

    image_count = len(images)
    if image_count > 1:
        # TODO: Translate
        options.append( [['View all {} pictures'.format(len(images)), browse_product]] )
        params.append( [str(product.id), str(product.model), str('True')] )

    # TODO: Translate
    options.append( [['Add to Shopping Cart'.format(len(images)), _start_add_to_cart]] )
    params.append( [str(product.id), str(product.model)] )


    options.append( [[t.action_back, browse_catalog]] )
    params.append( [str(product.catalog_ref), str(cctxt.catalog_page)] )
    return options, params


@requires_registered
def catalogs(model, ctxt, chat, args):
# TODO: List public catalogs for unregistered users
    list_user_catalogs(model, ctxt, chat, args)


def list_user_catalogs(model, ctxt, chat, args):
    conn = model.db()
    # TODO: Paginate
    catalogs = Catalog.for_user(conn, ctxt.user_id)
    options, params = _menu_catalogs(model.cfg.t, ctxt, catalogs)
    conn.close()

    chat.clean_options()
    chat.replyTemplate('catalog/list', options, params)


@requires_registered
def browse_catalog(model, ctxt, chat, text):
    args = text.split()

    catalog_id = int(args[0])
    if catalog_id is None:
        return

    page = 0
    if len(args) > 1:
        page = int(args[1])
        if page is None:
            return

    _browse_catalog_page(model, ctxt, chat, catalog_id = catalog_id, page = page, update = False)


@requires_registered
def _update_catalog_page(model, ctxt, chat, args):
    page = int(args)
    if page is None:
        return

    _browse_catalog_page(model, ctxt, chat, page = page)


@requires_registered
def _browse_catalog_page(model, ctxt, chat, catalog_id = None, page = None, update = True):
    cctxt = ctxt.conversations.current().ctxt

    if catalog_id is not None:
        cctxt.catalog_id = catalog_id

    if page is not None:
        cctxt.catalog_page = page

    if cctxt.catalog_id is None:
        return

    if cctxt.catalog_page is None:
        return


    conn = model.db()
    catalog = Catalog.by_id_for(conn, cctxt.catalog_id, ctxt.user_id)
    options, params = _options_for_page(conn, model.cfg.t, catalog, chat, cctxt.catalog_page)

    if options:
        if update:
            chat.update_options(options, params)
        else:
            chat.clean_options()
            chat.replyTemplate('catalog/catalog', options, params, catalog = catalog)

    conn.close()


def _options_for_page(conn, t, catalog, chat, page):
    page_size = 5 # TODO: Get this from chat, may be different per interface.
    pages = ceil(catalog.product_count(conn) / page_size)

    if page is None or page < 0 or page >= pages:
        return None, None

    products = catalog.product_page(conn, page, page_size)
    options, params = _menu_products(t, products, page, pages)

    return options, params


@requires_registered
def browse_product(model, ctxt, chat, text):
    args = text.split()
    _browse_product(model, ctxt, chat, int(args[0]), int(args[1]), args[2] == 'True')


def _browse_product(model, ctxt, chat, product_id = None, product_model = None, all_photos = False):
    cctxt = ctxt.conversations.current().ctxt

    if product_id is not None:
        cctxt.product_id = product_id

    if product_model is not None:
        cctxt.product_model = product_model

    if all_photos is not None:
        cctxt.all_photos = all_photos

    if cctxt.catalog_id is None:
        return

    if cctxt.product_id is None:
        return

    if cctxt.all_photos is None:
        return

    conn = model.db()
    product = Product.by_id_from_catalog_for(conn, cctxt.product_id, cctxt.product_model, cctxt.catalog_id, ctxt.user_id)
    images = model.uploads.photos_for_product(cctxt.catalog_id, cctxt.product_id)
    options, params = _menu_product(model.cfg.t, product, images, cctxt)

    chat.clean_options()

    if cctxt.all_photos:
        for photo in images:
            chat.replyPhoto(photo)
    else:
        chat.replyPhoto(images[0])

    chat.replyTemplate('catalog/product', options, params, product = product)
    conn.close()


@requires_registered
def _start_add_to_cart(model, ctxt, chat, text):
    conversation, entry = cart.add_product_conversation()

    chat.clean_options()

    args = text.split()
    product_id = int(args[0])
    product_model = int(args[1])

    if product_id is None:
        return
    if product_model is None:
        return

    ctxt.conversations.current().ctxt.product_id = product_id
    ctxt.conversations.current().ctxt.product_model = product_model
    ctxt.conversations.current().ctxt.all_photos = False
    ctxt.conversations.current().resume = _browse_product

    ctxt.conversations.start(conversation)

    chat.clean_options()
    entry(model, ctxt, chat, text)
