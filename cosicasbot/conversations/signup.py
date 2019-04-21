#!/usr/bin/env python
# -*- coding: utf-8 -*-

from ..filters import *
from . import start
from ..model.entities import *

__name__ = 'Signup'

def _commands():
    return [
        signup,

    # Private commands
        _signup_ask_name,
        _signup_ask_lastname,
        _signup_ask_email,
        _signup_ask_phone,
        _signup_ask_vat,
        _signup_ask_invoicing,
        _signup_ask_shipping,

        _signup_name,
        _signup_lastname,
        _signup_email,
        _signup_phone,
        _signup_vat,
        _signup_invoicing,
        _signup_shipping
    ]


def _menu_registering_options(t, ctxt):
    options = [
        [[t.action_start, start.start]],
        [[t.action_cancel, start.cancel]]
    ]

    return options


def _menu_registered_options(t, ctxt):
    options = [
        [[t.action_signup_edit_name, _signup_ask_name]],
        [[t.action_signup_edit_last_name, _signup_ask_lastname]],
        [[t.action_signup_edit_email, _signup_ask_email]],
        [[t.action_signup_edit_phone, _signup_ask_phone]],
        [[t.action_signup_edit_vat, _signup_ask_vat]],
        [[t.action_signup_edit_invoicing, _signup_ask_invoicing]],
        [[t.action_signup_edit_shipping, _signup_ask_shipping]],
        [[t.action_do_nothing, start.cancel]]
    ]

    return options


def signup(model, ctxt, chat, args):

    # If it's a new user, create the new user and start asking for data.
    # Else, let's see what data is missing.
    # If no data is missing, ask to edit the data.
    if not ctxt.user_id:
        # Create an empty user object
        conn = model.db()
        user = User.default_user()
        chat.fill_user(user)

        conn.add(user)
        conn.commit()

        # Migrate user to a new registered user context
        new_ctxt = model.ctxt(user.id)
        for key, value in ctxt.getData().items():
            if key == 'visitor_id':
                continue
            setattr(new_ctxt, key, value)

        _signup_ask_name(model, new_ctxt, chat, args, initial_signup=True)
        return

    conn = model.db()
    user = User.by_id(conn, ctxt.user_id)
    userdata = chat.render('signup/_userdata', user=user)

    if not user.lastname:
        _signup_ask_lastname(model, ctxt, chat, args, userdata=userdata)

    elif not user.email_address:
        _signup_ask_email(model, ctxt, chat, args, userdata=userdata)

    elif not user.phone_number:
        _signup_ask_phone(model, ctxt, chat, args, userdata=userdata)

    elif not user.vat_id:
        _signup_ask_vat(model, ctxt, chat, args, userdata=userdata)

    elif not user.invoice_address:
        _signup_ask_invoicing(model, ctxt, chat, args, userdata=userdata)

    elif not user.shipping_address:
        _signup_ask_shipping(model, ctxt, chat, args, userdata=userdata)

    else:
        chat.replyTemplate('signup/show_registered_user', _menu_registered_options(model.cfg.t, ctxt), [], userdata=userdata)

    conn.close()


@requires_registered
def _signup_ask_name(model, ctxt, chat, text, initial_signup = False):
    ctxt.next_text = _signup_name
    chat.replyTemplate('signup/ask_name', _menu_registering_options(model.cfg.t, ctxt), show_preamble=initial_signup)
    return


@requires_registered
def _signup_ask_lastname(model, ctxt, chat, text, userdata = None):
    ctxt.next_text = _signup_lastname
    chat.replyTemplate('signup/ask_lastname', _menu_registering_options(model.cfg.t, ctxt), userdata=userdata)


@requires_registered
def _signup_ask_email(model, ctxt, chat, text, userdata = None):
    ctxt.next_text = _signup_email
    chat.replyTemplate('signup/ask_email', _menu_registering_options(model.cfg.t, ctxt), userdata=userdata)


@requires_registered
def _signup_ask_phone(model, ctxt, chat, text, userdata = None):
    ctxt.next_text = _signup_phone
    chat.replyTemplate('signup/ask_phone', _menu_registering_options(model.cfg.t, ctxt), userdata=userdata)


@requires_registered
def _signup_ask_vat(model, ctxt, chat, text, userdata = None):
    ctxt.next_text = _signup_vat
    chat.replyTemplate('signup/ask_vat', _menu_registering_options(model.cfg.t, ctxt), userdata=userdata)


@requires_registered
def _signup_ask_invoicing(model, ctxt, chat, text, userdata = None):
    ctxt.next_text = _signup_invoicing
    chat.replyTemplate('signup/ask_invoicing', _menu_registering_options(model.cfg.t, ctxt), userdata=userdata)


@requires_registered
def _signup_ask_shipping(model, ctxt, chat, text, userdata = None):
    ctxt.next_text = _signup_shipping
    chat.replyTemplate('signup/ask_shipping', _menu_registering_options(model.cfg.t, ctxt), userdata=userdata)


@requires_registered
@requires_text_length(length=3)
def _signup_name(model, ctxt, chat, text):

    conn = model.db()

    user = User.by_id(conn, ctxt.user_id)
    user.name = text.strip()

    conn.commit()
    conn.close()

    return signup(model, ctxt, chat, None)


@requires_registered
@requires_text_length(length=3)
def _signup_lastname(model, ctxt, chat, text):

    conn = model.db()

    user = User.by_id(conn, ctxt.user_id)
    user.lastname = text.strip()

    conn.commit()
    conn.close()

    return signup(model, ctxt, chat, None)


@requires_registered
@requires_text_length(length=3)
def _signup_email(model, ctxt, chat, text):

    conn = model.db()

    user = User.by_id(conn, ctxt.user_id)
    user.email_address = text.strip()

    conn.commit()
    conn.close()

    return signup(model, ctxt, chat, None)


@requires_registered
@requires_text_length(length=3)
def _signup_phone(model, ctxt, chat, text):

    conn = model.db()

    user = User.by_id(conn, ctxt.user_id)
    user.phone_number = text.strip()

    conn.commit()
    conn.close()

    return signup(model, ctxt, chat, None)


@requires_registered
@requires_text_length(length=3)
def _signup_vat(model, ctxt, chat, text):

    conn = model.db()

    user = User.by_id(conn, ctxt.user_id)
    user.vat_id = text.strip()

    conn.commit()
    conn.close()

    return signup(model, ctxt, chat, None)


@requires_registered
@requires_text_length(length=3)
def _signup_invoicing(model, ctxt, chat, text):

    conn = model.db()

    user = User.by_id(conn, ctxt.user_id)
    user.invoice_address = text.strip()

    conn.commit()
    conn.close()

    return signup(model, ctxt, chat, None)


@requires_registered
@requires_text_length(length=3)
def _signup_shipping(model, ctxt, chat, text):

    conn = model.db()

    user = User.by_id(conn, ctxt.user_id)
    user.shipping_address = text.strip()

    conn.commit()
    conn.close()

    return signup(model, ctxt, chat, None)

