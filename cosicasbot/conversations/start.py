#!/usr/bin/env python
# -*- coding: utf-8 -*-

from ..filters import *
from . import signup
from ..model.entities import *

__name__ = 'Start'

def _commands():
    return [
        start,
        browse_catalogs,
        cancel,

# Test commands
        count,      # Test sessions
        secret      # Test filters

# Private commands
    ]


def _menu_start_options(t, ctxt):
    options = [
        [[t.action_do_nothing, cancel]],
        [[t.action_browse_catalogs, browse_catalogs]]
    ]

    if not ctxt.user_id:
        options.append( [[t.action_signup, signup.signup]] )
    else:
        options.append( [[t.action_signup_edit, signup.signup]] )

    return options

def start(model, ctxt, chat, args):
    chat.replyTemplate('start', _menu_start_options(model.cfg.t, ctxt), [], model=model, ctxt=ctxt, chat=chat)


def cancel(model, ctxt, chat, text):
    ctxt.clean_next()
    chat.replyText('Genial, cuando quieras hablar conmigo usa /start.')


def browse_catalogs(model, ctxt, chat, text):
    chat.replyText('Estas son tus tiendas:')


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

