#!/usr/bin/env python
# -*- coding: utf-8 -*-

from ..filters import *
from . import start
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

    chat.replyTemplate('catalog/list', options, params)


@requires_registered
def browse_catalog(model, ctxt, chat, args):
    chat.replyText(args)
