#!/usr/bin/env python
# -*- coding: utf-8 -*-

import functools


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


def requires_text_length(length):
    def inner(func):
        @functools.wraps(func)
        def wrapper_decorator(*args, **kwargs):
            model = args[0]
            ctxt = args[1]
            chat = args[2]
            text = args[3]
            t = model.cfg.t

            if not len(text.strip()) > length:
                chat.replyText(t.error_require_text_length.format(length))
                return

            value = func(*args, **kwargs)
            return value
        return wrapper_decorator
    return inner
