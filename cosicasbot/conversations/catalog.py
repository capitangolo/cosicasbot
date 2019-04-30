#!/usr/bin/env python
# -*- coding: utf-8 -*-

from ..filters import *
from . import start
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
        options.append( [[ '⏪', _browse_page ]] )
        params.append( [str( page - 1)] )

    for product in products:
        # TODO: Localize the price format
        title = "{} {:.02f}€".format(product.name, product.price)
        options.append( [[title, browse_product]] )
        params.append( [str(product.id), str(product.model)] )

    if page < page_count - 1:
        options.append( [[ '⏩', _browse_page ]] )
        params.append( [str( page + 1)] )


    options.append( [[t.action_back, catalogs]] )
    params.append( [] )
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
def browse_catalog(model, ctxt, chat, args):
    cctxt = ctxt.conversations.current().ctxt
    cctxt.catalog_id = int(args)

    if not cctxt.catalog_id:
        return

    conn = model.db()
    catalog = Catalog.by_id_for(conn, cctxt.catalog_id, ctxt.user_id)
    options, params = _options_for_page(conn, model.cfg.t, catalog, chat, 0)

    if options:
        chat.clean_options()
        chat.replyTemplate('catalog/catalog', options, params, catalog = catalog)

    conn.close()


@requires_registered
def _browse_page(model, ctxt, chat, args):
    cctxt = ctxt.conversations.current().ctxt

    if not cctxt.catalog_id:
        return

    page = int(args)
    if page is None:
        return

    conn = model.db()
    catalog = Catalog.by_id_for(conn, cctxt.catalog_id, ctxt.user_id)
    options, params = _options_for_page(conn, model.cfg.t, catalog, chat, page)
    conn.close()

    if options:
        chat.update_options(options, params)


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
    cctxt = ctxt.conversations.current().ctxt
    cctxt.product_id = int(args[0])
    cctxt.product_model = int(args[1])

    if not cctxt.catalog_id:
        return

    if not cctxt.product_id:
        return

    conn = model.db()
    product = Product.by_id_from_catalog_for(conn, cctxt.product_id, cctxt.product_model, cctxt.catalog_id, ctxt.user_id)
#    options, params = _options_for_page(conn, model.cfg.t, catalog, chat, 0)

#    if options:
#    chat.clean_options()
    chat.replyTemplate('catalog/product', product = product)
    conn.close()

    images = model.uploads.photos_for_product(cctxt.catalog_id, cctxt.product_id)
    if images:
        chat.replyPhoto(images[0])

