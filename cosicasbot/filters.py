#!/usr/bin/env python
# -*- coding: utf-8 -*-

import functools


def requires_registered(func):
    @functools.wraps(func)
    def wrapper_decorator(*args, **kwargs):
        model = args[0]
        ctxt = args[1]
        chat = args[2]

        user = ctxt.user
        if not user:
            # TODO: remove text from here
            chat.replyText('Necesitas estar registrado para ejecutar {}'.format(chat.screen_command(func.__name__)))
            return

        value = func(*args, **kwargs)
        return value
    return wrapper_decorator


