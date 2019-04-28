#!/usr/bin/env python
# -*- coding: utf-8 -*-

from ..filters import *
from . import signup
from ..model.context import Conversation
from ..model.entities import *

__name__ = 'AdminUsers'

def _commands():
    return [
        start_admin,
    ]


def admin_conversation():
    return Conversation(), start_admin


def _end_admin(model, ctxt, chat, args):
    ctxt.conversations.end(model, ctxt, chat, args)


def _menu_start_admin(t, ctxt):
    options = [
        [[t.action_list_users, _list_users]],
        [[t.action_back, _end_admin]]
    ]

    return options


@requires_superadmin
def start_admin(model, ctxt, chat, args):
    chat.clean_options()
    chat.replyTemplate('admin/start', _menu_start_admin(model.cfg.t, ctxt), [])


@requires_superadmin
def _list_users(model, ctxt, chat, args):
    conn = model.db()

    # TODO: Paginate
    display_groups = []
    groups = conn.query(UserGroup).all()
    for group in groups:
        users = []
        for user in group.users:
            role = Role.for_user_in_group(conn, user.id, group.id)
            role_name = ''
            if role and role != RoleLevel.user:
                role_name = " ({})".format(role.role.name)
            users.append({'user': user, 'role_name': role_name, 'username': chat.screen_username(user)})
        display_groups.append({'group': group, 'users': users})

    conn.close()

    chat.clean_options()
    chat.replyTemplate('admin/userlist', title = 'All users', groups = display_groups)
    start_admin(model, ctxt, chat, args)
