#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
from ..filters import *
from . import signup
from ..model.context import Conversation
from ..model.entities import *
from operator import itemgetter

__name__ = 'AdminUsers'

def _commands():
    return [
        start_admin,
    ]


def admin_orders_conversation():
    return Conversation(), select_catalog


def _end_admin(model, ctxt, chat, args):
    ctxt.conversations.end(model, ctxt, chat, args)


def _menu_catalogs(t, ctxt, catalogs):
    options = []
    params = []

    for catalog in catalogs:
        options.append( [[catalog.name, browse_catalog]] )
        params.append( [str(catalog.id)] )

    options.append( [[t.action_back, _end_admin]] )
    params.append( [] )
    return options, params


def select_catalog(model, ctxt, chat, args):
    conn = model.db()

    catalogs = Catalog.for_admin_user(conn, ctxt.user_id)
    options, params = _menu_catalogs(model.cfg.t, ctxt, catalogs)

    conn.close()

    chat.clean_options()
    chat.replyTemplate('orders_admin/select_catalog', options, params)


def browse_catalog(model, ctxt, chat, text):
    args = text.split()

    catalog_id = int(args[0])
    if catalog_id is None:
        return

    ctxt.catalog_id = catalog_id
    _browse_catalog(model, ctxt, chat)


def _menu_admin_catalog(t, ctxt):
    options = [
        [[ t.action_admin_orders_list_orders, download_open_orders ]],
        [[ t.action_admin_orders_list_products, download_product_sumary ]],
        [[ "USER SUMMARY", download_product_summary_per_user ]],
        [[ t.action_admin_orders_list_carts, download_cartitems ]],
        [[ t.action_admin_orders_dowload_masters, download_masters ]],
    ]

    options.append( [[t.action_back, select_catalog]] )
    return options


@requires_catalog_admin
def _browse_catalog(model, ctxt, chat):
    conn = model.db()
    catalog = conn.query(Catalog).get(ctxt.catalog_id)

    t = model.cfg.t
    options = _menu_admin_catalog(t, ctxt)

    chat.clean_options()
    chat.replyTemplate('orders_admin/browse_catalog', options, [], catalog = catalog)

    conn.close()



@requires_catalog_admin
def download_open_orders(model, ctxt, chat, txt):
    conn = model.db()

    orders = Order.open_for_catalog(conn, ctxt.catalog_id)

    data = [['order', 'status', 'user', 'telegram', 'invoice_address', 'shipping_address', 'product', 'model', 'name', 'price', 'tax', 'quantity', 'net_subtotal']]
    for order in orders:
        for lineitem in order.lineitems:
            data.append([
                order.id,
                order.status_display(model.cfg.t),
                order.user_ref,
                order.user.telegram_handle,
                order.invoice_to,
                order.ship_to,
                lineitem.product_ref,
                lineitem.product_model,
                lineitem.product.name,
                lineitem.price,
                lineitem.tax,
                lineitem.quantity,
                lineitem.price * lineitem.quantity,
            ])
        data.append([
            order.id,
            order.status_display(model.cfg.t),
            order.user_ref,
            order.user.telegram_handle,
            order.invoice_to,
            order.ship_to,
            0,
            0,
            "Shipping",
            order.shipping_price,
            order.shipping_tax,
            1,
            order.shipping_price,
        ])


    filename = "{}_{}_{}.csv".format("orders", ctxt.catalog_id, datetime.datetime.now().strftime('%Y%m%d%H%M%S'))
    chat.replyCSV(data, filename)


@requires_catalog_admin
def download_product_sumary(model, ctxt, chat, txt):
    conn = model.db()

    orders = Order.open_for_catalog(conn, ctxt.catalog_id)

    summary = {}
    for order in orders:
        for lineitem in order.lineitems:
            if not lineitem.product_ref in summary:
                summary[lineitem.product_ref] = {}

            if not lineitem.product_model in summary[lineitem.product_ref]:
                summary[lineitem.product_ref][lineitem.product_model] = {
                    'quantity': 0,
                    'name': lineitem.product.name
                }

            summary[lineitem.product_ref][lineitem.product_model]['quantity'] += lineitem.quantity

    data = []
    for product_id, product in summary.items():
        for model_id, model in product.items():
            data.append([
                product_id,
                model_id,
                model['name'],
                model['quantity'],
            ])

    data = sorted(data, key=itemgetter(2))
    data.insert(0, ['product', 'model', 'name', 'quantity'])

    filename = "{}_{}_{}.csv".format("summary", ctxt.catalog_id, datetime.datetime.now().strftime('%Y%m%d%H%M%S'))
    chat.replyCSV(data, filename)



@requires_catalog_admin
def download_product_summary_per_user(model, ctxt, chat, txt):
    conn = model.db()

    orders = Order.open_for_catalog(conn, ctxt.catalog_id)

    summary = {}
    keys = ['user', 'telegram', 'filter_tag']
    for order in orders:
        for lineitem in order.lineitems:
            if not lineitem.product_ref in keys:
                keys.append(lineitem.product_ref)

            filter_tag = lineitem.product.filter_tag_value
            order_key = "{}_{}".format(order.user_ref, filter_tag)
            if order_key not in summary:
                summary[order_key] = {
                        'user': order.user_ref,
                        'telegram': order.user.telegram_handle,
                        'filter_tag': filter_tag
                    }
            user_summary = summary[order_key]

            quantity = lineitem.quantity
            if lineitem.product_ref in user_summary:
                quantity += user_summary[lineitem.product_ref]

            user_summary[lineitem.product_ref] = quantity

    data = [ keys ]
    for user_key, user_summary in summary.items():
        data_line = []
        for key in keys:
            if key in user_summary:
                data_line.append(user_summary[key])
            else:
                data_line.append('')
        data.append(data_line)

    filename = "{}_{}_{}.csv".format("user_summary", ctxt.catalog_id, datetime.datetime.now().strftime('%Y%m%d%H%M%S'))
    chat.replyCSV(data, filename)


@requires_catalog_admin
def download_cartitems(model, ctxt, chat, txt):
    conn = model.db()

    items = CartItem.for_catalog(conn, ctxt.catalog_id)

    data = [['user', 'telegram', 'product', 'model', 'name', 'price', 'tax', 'quantity', 'net_subtotal']]
    for item in items:
        data.append([
            item.user_ref,
            item.user.telegram_handle,
            item.product_ref,
            item.product_model,
            item.product.name,
            item.product.price,
            item.product.tax,
            item.quantity,
            item.product.price * item.quantity,
        ])

    filename = "{}_{}_{}.csv".format("cartitems", ctxt.catalog_id, datetime.datetime.now().strftime('%Y%m%d%H%M%S'))
    chat.replyCSV(data, filename)



@requires_catalog_admin
def download_masters(model, ctxt, chat, txt):
    conn = model.db()

    orders = Order.open_for_catalog(conn, ctxt.catalog_id)

    products = set()
    for order in orders:
        for lineitem in order.lineitems:
            products.add(lineitem.product)

    zipfile, missing = model.zip_masters_for(products)

    chat.replyTemplate('orders_admin/missing_masters', missing=missing)

    conn.close()

    filename = "{}_{}_{}.zip".format("masters", ctxt.catalog_id, datetime.datetime.now().strftime('%Y%m%d%H%M%S'))
    chat.replyDocument(zipfile, filename)

