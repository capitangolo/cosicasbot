#!/usr/bin/env python
# -*- coding: utf-8 -*-

from ..filters import *

__name__ = 'Start'


def _commands():
    return [
        start,
        count,
        secret
    ]


def _menu_start_options():
    return {
        'list': [
            [['A', _menu_a]],
            [['B', _menu_b]],
            [['C', _menu_c]]
        ],
        'inline': False
    }


def start(model, ctxt, chat):
    ctxt.next_text = _process_menu
    chat.replyTemplate('start', options=_menu_start_options(), model=model, ctxt=ctxt, chat=chat)


def _process_menu(model, ctxt, chat, text):
    callback = chat.callback_for_input(_menu_start_options(), text)
    if callback:
        ctxt.next_text = None
        callback(model, ctxt, chat, text)


def _menu_a(model, ctxt, chat, text):
    chat.replyText('Esto es A')

def _menu_b(model, ctxt, chat, text):
    chat.replyText('Esto es B')

def _menu_c(model, ctxt, chat, text):
    chat.replyText('Esto es C')


def count(model, ctxt, chat):
    if not ctxt.number:
        ctxt.number = 1
    else:
        ctxt.number += 1
    chat.replyText('Hola {}!'.format(ctxt.number))


@requires_registered
def secret(model, ctxt, chat):
    chat.replyText('¡Hola {} {}!'.format(ctxt.user.name, ctxt.user.lastname))

