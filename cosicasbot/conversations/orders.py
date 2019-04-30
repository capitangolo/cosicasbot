#!/usr/bin/env python
# -*- coding: utf-8 -*-

from ..filters import *
from . import start
from ..model.context import Conversation
from ..model.entities import *

__name__ = 'Orders'

def _commands():
    return [
        orders,
        browse_order
    ]


def orders_conversation():
    return Conversation(), orders


def _end_orders(model, ctxt, chat, args):
    ctxt.conversations.end(model, ctxt, chat, args)


def _menu_orders(t, ctxt, orders):
    options = []
    params = []

    for order in orders:
        title = "#{} {} {:.2f}€ - {}".format(order.id, order.catalog.name, order.total(), order.status_display(t))
        options.append( [[title, browse_order]] )
        params.append( [str(order.id)] )

    options.append( [[t.action_back, _end_orders]] )
    params.append( [] )
    return options, params


def _menu_browse_order(t, ctxt, order):
    options = []
    params = []

    # TODO: Translate
    if order.status is OrderStatus.received:
        options.append( [['Cancel', confirm_cancel_order]] )
        params.append( [str(order.id)] )

    options.append( [[t.action_back, orders]] )
    params.append( [] )
    return options, params


def _menu_confirm_cancel_order(t, ctxt, order):
    options = []
    params = []

    # TODO: Translate
    options.append( [['Cancel Order', cancel_order]] )
    params.append( [str(order.id)] )

    options.append( [[t.action_back, browse_order]] )
    params.append( [str(order.id)] )
    return options, params


@requires_registered
def orders(model, ctxt, chat, args):
    conn = model.db()
    # TODO: Paginate
    orders = Order.for_user(conn, ctxt.user_id)
    options, params = _menu_orders(model.cfg.t, ctxt, orders)
    conn.close()

    chat.clean_options()
    chat.replyTemplate('orders/list', options, params, orders = orders)


@requires_registered
def browse_order(model, ctxt, chat, args):
    order_id = int(args)

    conn = model.db()
    order = conn.query(Order).filter_by(id = order_id, user_ref = ctxt.user_id).one()

    if not order:
        return

    options, params = _menu_browse_order(model.cfg.t, ctxt, order)

    chat.clean_options()
    status = order.status_display(model.cfg.t)
    chat.replyTemplate('orders/order', options, params, order = order, status = status)
    conn.close()


@requires_registered
def confirm_cancel_order(model, ctxt, chat, args):
    order_id = int(args)

    conn = model.db()
    order = conn.query(Order).filter_by(id = order_id, user_ref = ctxt.user_id, status = OrderStatus.received).one()

    if not order:
        return

    options, params = _menu_confirm_cancel_order(model.cfg.t, ctxt, order)

    chat.clean_options()
    status = order.status_display(model.cfg.t)
    chat.replyTemplate('orders/confirm_cancel', options, params, order = order)
    conn.close()


@requires_registered
def cancel_order(model, ctxt, chat, args):
    order_id = int(args)

    conn = model.db()
    order = conn.query(Order).filter_by(id = order_id, user_ref = ctxt.user_id, status = OrderStatus.received).one()

    if not order:
        return

    for lineitem in order.lineitems:
        cartitem = conn.query(CartItem).get( [ctxt.user_id, lineitem.product_ref, lineitem.product_model] )
        if not cartitem:
            cartitem = CartItem(
                    user_ref = ctxt.user_id,
                    product_ref = lineitem.product_ref,
                    product_model = lineitem.product_model,
                    quantity = 0
            )
            conn.add(cartitem)
        cartitem.quantity += lineitem.quantity
        conn.delete(lineitem)
        conn.commit()

    conn.delete(order)
    conn.commit()
    conn.close()

    orders(model, ctxt, chat, args)
