#!/usr/bin/env python
# -*- coding: utf-8 -*-

from . import start, catalog
from decimal import Decimal
from ..filters import *
from math import ceil
from ..model.context import Conversation
from ..model.entities import *

__name__ = 'Cart'

def _commands():
    return [
        add_to_cart
    ]


def check_cart_conversation():
    return Conversation(), check_cart


def add_product_conversation():
    return Conversation(), add_to_cart


def _end_conversation(model, ctxt, chat, args):
    ctxt.conversations.end(model, ctxt, chat, args)


@requires_registered
def check_cart(model, ctxt, chat, text):
    conn = model.db()

    # TODO: Set this as a setting
    shipping_tax = Decimal('0.21')

    items = conn.query(CartItem).filter_by(user_ref = ctxt.user_id).all()
    catalogs_by_id = {}
    for item in items:
        catalog_id = item.product.catalog_ref
        if catalog_id not in catalogs_by_id:
            catalog = {
                'name': item.product.catalog.name,
                'items': [],
                'subtotal': Decimal('0'),
                'shipping': Decimal('0'),
                'tax': Decimal('0'),
                'total': Decimal('0')
            }
            catalogs_by_id[catalog_id] = catalog

        catalog = catalogs_by_id[catalog_id]
        catalog['subtotal'] += item.product.price * item.quantity
        catalog['tax'] += item.product.price * item.quantity * item.product.tax
        catalog['total'] += item.product.price * item.quantity * ( 1 + item.product.tax )
        catalog['items'].append(item)

    for catalog in catalogs_by_id.values():
        shipping = Order._shipping_price(catalog['subtotal'])
        catalog['shipping'] = shipping
        catalog['tax'] += shipping * shipping_tax
        catalog['total'] += shipping * (1 + shipping_tax)

    user = conn.query(User).get(ctxt.user_id)

    t = model.cfg.t
    options = [
        [[t.action_cart_checkout, checkout]],
        [[t.action_cart_clear, clear_cart]],
        [[t.action_back, _end_conversation]]
    ]
    chat.replyTemplate('cart/cart', options, [], items = items, catalogs = catalogs_by_id.values(), user = user)

    conn.close()


@requires_registered
def checkout(model, ctxt, chat, text):
    conn = model.db()

    # TODO: Set this as a setting
    shipping_tax = Decimal('0.21')

    items = conn.query(CartItem).filter_by(user_ref = ctxt.user_id).all()
    catalogs_by_id = {}
    for item in items:
        catalog_id = item.product.catalog_ref
        if catalog_id not in catalogs_by_id:
            catalog = {
                'name': item.product.catalog.name,
                'items': [],
                'subtotal': Decimal('0'),
                'shipping': Decimal('0'),
                'tax': Decimal('0'),
                'total': Decimal('0')
            }
            catalogs_by_id[catalog_id] = catalog

        catalog = catalogs_by_id[catalog_id]
        catalog['subtotal'] += item.product.price * item.quantity
        catalog['tax'] += item.product.price * item.quantity * item.product.tax
        catalog['total'] += item.product.price * item.quantity * ( 1 + item.product.tax )
        catalog['items'].append(item)

    user = conn.query(User).get(ctxt.user_id)
    invoice_to = "{} {}\n{}\n{}".format(user.name, user.lastname, user.vat_id, user.invoice_address)
    ship_to = "{} {}\n{}\n{}\n{}".format(user.name, user.lastname, user.email_address, user.phone_number, user.shipping_address)

    orders = []
    for catalog_id, catalog in catalogs_by_id.items():
        shipping = Order._shipping_price(catalog['subtotal'])
        catalog['tax'] += shipping * shipping_tax
        catalog['total'] += shipping * (1 + shipping_tax)

        # TODO: Include subtotal, tax and total in Order.
        order = Order(
            user_ref = user.id,
            catalog_ref = catalog_id,
            status = OrderStatus.received,
            shipping_price = shipping,
            shipping_tax = shipping_tax,
            invoice_to = invoice_to,
            ship_to = ship_to
        )
        conn.add(order)

        for cart_item in catalog['items']:
            lineitem = LineItem(
                order = order,
                product_ref = cart_item.product.id,
                product_model = cart_item.product.model,
                price = cart_item.product.price,
                tax = cart_item.product.tax,
                quantity = cart_item.quantity
            )
            conn.add(lineitem)
            conn.delete(cart_item)
        conn.commit()
        orders.append(order)

    t = model.cfg.t
    options = [
        [[t.action_back, _end_conversation]]
    ]
    chat.replyTemplate('cart/confirm_checkout', options, [], orders = orders)

    conn.close()


@requires_registered
def clear_cart(model, ctxt, chat, text):
    conn = model.db()
    conn.query(CartItem).filter_by(user_ref = ctxt.user_id).delete()
    conn.commit()
    conn.close()

    _end_conversation(model, ctxt, chat, text)


@requires_registered
def add_to_cart(model, ctxt, chat, text):
    args = text.split()
    product_id = int(args[0])
    product_model = int(args[1])
    quantity = None

    if len(args) > 2:
        quantity = int(args[2])

    _add_to_cart(model, ctxt, chat, product_id, product_model, quantity)


def _add_to_cart(model, ctxt, chat, product_id, product_model, quantity):
    if product_id is None:
        return

    if product_model is None:
        return

    if quantity is None:
        _ask_quantity(model, ctxt, chat, product_id, product_model)
        return

    conn = model.db()
    item = conn.query(CartItem).get([ctxt.user_id, product_id, product_model])
    if not item:
        item = CartItem(user_ref = ctxt.user_id, product_ref = product_id, product_model = product_model, quantity = quantity)
        conn.add(item)
    else:
        item.quantity = quantity
    conn.commit()

    product = item.product

    chat.clean_options()
    t = model.cfg.t
    # TODO: Option to review shopping cart
    options = [ [[t.action_back, _end_conversation]] ]
    chat.replyTemplate('cart/added_product', options, [], product = product, quantity = item.quantity)

    conn.close()


@requires_registered
def _ask_quantity(model, ctxt, chat, product_id, product_model):
    conversation = ctxt.conversations.current()
    cctxt = conversation.ctxt

    cctxt.product_id = product_id
    cctxt.product_model = product_model

    conversation.next_text = _read_quantity

    conn = model.db()

    product = conn.query(Product).get([product_id, product_model])
    item = conn.query(CartItem).get([ctxt.user_id, product_id, product_model])

    chat.clean_options()
    t = model.cfg.t
    options = [ [[t.action_cancel, _end_conversation]] ]
    chat.replyTemplate('cart/ask_quantity', options, [], product = product, item = item)

    conn.close()


@requires_registered
def _read_quantity(model, ctxt, chat, text):
    quantity = int(text)
    cctxt = ctxt.conversations.current().ctxt

    if not quantity or quantity < 1:
        _ask_quantity(model, ctxt, chat, cctxt.product_id, cctxt.product_model)
        return

    _add_to_cart(model, ctxt, chat, cctxt.product_id, cctxt.product_model, quantity)
