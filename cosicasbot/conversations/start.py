#!/usr/bin/env python
# -*- coding: utf-8 -*-

from ..filters import *

__name__ = 'Start'


def _commands():
    return [
        start,
        count,
        secret,
        signup,

# Private commands
        _do_nothing,
        _browse_catalogs
    ]


def _menu_start_options(model, ctxt):
    t = model.cfg.t
    options = [
        [[t.action_do_nothing, _do_nothing]],
        [[t.action_browse_catalogs, _browse_catalogs]]
    ]

    if not ctxt.user:
        options.append(
            [[t.action_signup, signup]]
        )
    return options

def start(model, ctxt, chat, args):
    chat.replyTemplate('start', _menu_start_options(model, ctxt), [], model=model, ctxt=ctxt, chat=chat)


def _do_nothing(model, ctxt, chat, text):
    chat.replyText('Genial, cuando quieras hablar conmigo usa /start.')


def _browse_catalogs(model, ctxt, chat, text):
    chat.replyText('Estas son tus tiendas:')


def signup(model, ctxt, chat, text):
    chat.replyText('¡Vamos a registrarnos!')


def count(model, ctxt, chat, args):
    if not ctxt.number:
        ctxt.number = 1
    else:
        ctxt.number += 1
    chat.replyText('Hola {}!'.format(ctxt.number))


@requires_registered
def secret(model, ctxt, chat, args):
    chat.replyText('¡Hola {} {}!'.format(ctxt.user.name, ctxt.user.lastname))

