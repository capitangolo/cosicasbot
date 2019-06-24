#!/usr/bin/env python
# -*- coding: utf-8 -*-

import functools
from .model.entities import *


def requires_registered(func):
    @functools.wraps(func)
    def wrapper_decorator(*args, **kwargs):
        model = args[0]
        ctxt = args[1]
        chat = args[2]
        t = model.cfg.t

        if not ctxt.user_id:
            chat.replyText(t.error_require_user.format(chat.screen_command(func.__name__)))
            return

        value = func(*args, **kwargs)
        return value
    return wrapper_decorator


def requires_superadmin(func):
    @functools.wraps(func)
    def wrapper_decorator(*args, **kwargs):
        model = args[0]
        ctxt = args[1]
        chat = args[2]
        t = model.cfg.t

        admin_group = model.cfg.groups_admin_id
        admin_role = RoleLevel.admin

        conn = model.db()
        is_admin = ctxt.user_id and Role.exists_for_user_in_group(conn, admin_role, ctxt.user_id, admin_group)
        conn.close()

        if not is_admin:
            # silently ignore, do not tip the command.
            model.log.warning("{} tried to access protected command {}.".format(chat.user_detail(), func.__name__))
            return

        value = func(*args, **kwargs)
        return value
    return wrapper_decorator


def requires_catalog_admin(func):
    @functools.wraps(func)
    def wrapper_decorator(*args, **kwargs):
        model = args[0]
        ctxt = args[1]
        chat = args[2]
        t = model.cfg.t

        conn = model.db()
        catalog = Catalog.count_by_id_for_admin(conn, ctxt.catalog_id, ctxt.user_id)
        conn.close()

        if not catalog:
            # silently ignore, do not tip the command.
            model.log.warning("{} tried to access protected command {}.".format(chat.user_detail(), func.__name__))
            return

        value = func(*args, **kwargs)
        return value
    return wrapper_decorator


def requires_text_length(length):
    def inner(func):
        @functools.wraps(func)
        def wrapper_decorator(*args, **kwargs):
            model = args[0]
            ctxt = args[1]
            chat = args[2]
            text = args[3]
            t = model.cfg.t

            if len(text.strip()) < length:
                chat.replyText(t.error_require_text_length.format(length))
                return

            value = func(*args, **kwargs)
            return value
        return wrapper_decorator
    return inner
