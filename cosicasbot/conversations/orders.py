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
        title = "#{} {} {:.2f}€ - {}".format(order.id, order.catalog().name, order.total(), order.status_display(t))
        options.append( [[title, browse_order]] )
        params.append( [str(order.id)] )

    options.append( [[t.action_back, _end_orders]] )
    params.append( [] )
    return options, params


def _menu_browse_order(t, ctxt):
    options = []
    options.append( [[t.action_back, orders]] )
    return options


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
    options = _menu_browse_order(model.cfg.t, ctxt)

    if not order:
        return

    chat.clean_options()
    status = order.status_display(model.cfg.t)
    chat.replyTemplate('orders/order', options, [], order = order, status = status)
    conn.close()

