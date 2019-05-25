#!/usr/bin/env python
# -*- coding: utf-8 -*-

from ..filters import *
from . import signup, catalog, admin, orders, cart
from ..model.context import Conversation
from ..model.entities import *

#TODO: Remove this dependency
from sqlalchemy import func

__name__ = 'Start'

def _commands():
    return [
        start,
        cancel,

# Test commands
        count,      # Test sessions
        secret      # Test filters
    ]


def start_conversation():
    return Conversation(cancel)


def _menu_start_options(t, ctxt, cart_items, is_admin):
    signup_text = t.action_signup_edit if ctxt.user_id else t.action_signup

    options = [
        [[t.action_browse_catalogs, _start_catalogs]],
        [[t.action_browse_orders, _start_orders]],
        [[signup_text, _start_signup]]
    ]

    if cart_items > 0:
        options.append( [[t.action_cart_browse.format(cart_items), _start_cart]] )

    if is_admin:
        options.append( [[t.action_admin, _start_admin]] )

    options.append( [[t.action_do_nothing, cancel]] )

    return options


def start(model, ctxt, chat, args):
    ctxt.conversations.hard_reset() # Discard all conversations when this command is executed

    conn = model.db()
    cart_items = conn.query(func.count(CartItem.user_ref)).filter_by(user_ref = ctxt.user_id).scalar()

    admin_group = model.cfg.groups_admin_id
    admin_role = RoleLevel.admin
    is_admin = ctxt.user_id and Role.exists_for_user_in_group(conn, admin_role, ctxt.user_id, admin_group)
    conn.close()

    chat.clean_options()
    chat.replyTemplate('start', _menu_start_options(model.cfg.t, ctxt, cart_items, is_admin), [], model=model, ctxt=ctxt, chat=chat)


def cancel(model, ctxt, chat, text):
    chat.clean_options()
    chat.replyTemplate('bye')


def _start_signup(model, ctxt, chat, text):
    conversation, entry = signup.signup_conversation()
    _start_conversation(conversation, entry, model, ctxt, chat, text)


def _start_catalogs(model, ctxt, chat, text):
    conversation, entry = catalog.catalogs_conversation()
    _start_conversation(conversation, entry, model, ctxt, chat, text)


@requires_registered
def _start_orders(model, ctxt, chat, text):
    conversation, entry = orders.orders_conversation()
    _start_conversation(conversation, entry, model, ctxt, chat, text)


@requires_registered
def _start_cart(model, ctxt, chat, text):
    conversation, entry = cart.check_cart_conversation()
    _start_conversation(conversation, entry, model, ctxt, chat, text)


@requires_superadmin
def _start_admin(model, ctxt, chat, text):
    conversation, entry = admin.admin_conversation()
    _start_conversation(conversation, entry, model, ctxt, chat, text)


def _start_conversation(conversation, entry, model, ctxt, chat, text):
    chat.clean_options()

    ctxt.conversations.current().resume = start

    ctxt.conversations.start(conversation)

    chat.clean_options()
    entry(model, ctxt, chat, text)




# =============
# Test Commands
# =============


def count(model, ctxt, chat, args):
    if not ctxt.number:
        ctxt.number = 1
    else:
        ctxt.number += 1
    chat.replyText('Hola {}!'.format(ctxt.number))



@requires_registered
def secret(model, ctxt, chat, args):
    conn = model.db()
    user = User.by_id(conn, ctxt.user_id)
    chat.replyText('¡Hola {} {}!'.format(user.name, user.lastname))
    conn.close()

