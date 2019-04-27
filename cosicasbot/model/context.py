#!/usr/bin/env python
# -*- coding: utf-8 -*-

from sqlalchemy.orm.util import class_mapper

class UserContexts:


    def __init__(self, user_id_property, start):
        self.user_id_property = user_id_property
        self.contexts = {}
        self.start_generator = start


    def context_for(self, user_id):
        if user_id not in self.contexts:
            self.contexts[user_id] = Context()
            setattr(self.contexts[user_id], self.user_id_property, user_id)
            conversations = ConversationStack()
            conversations.start(self.start_generator())
            setattr(self.contexts[user_id], 'conversations', conversations)
        return self.contexts[user_id]


class Context:


    def __init__(self):
        self.__dict__['__data'] = {}


    def __getattr__(self, name):
        if name in self.__dict__['__data']:
            return self.__dict__['__data'][name]
        return None


    def __setattr__(self, name, value):
        if self._is_sa_mapped(value):
            error = "Tried to store an ORM object in the context. This is a bad idea, store the id and fetch it later."
            raise(ProblematicValueError(value, error))
        self.__dict__['__data'][name] = value


    def __delattr__(self, name):
        if name in self.__dict__['__data']:
            del self.__dict__['__data'][obj]


    def has_key(self, key):
        return key in self.get_data()

    def get_data(self):
        return self.__dict__['__data']


    def _is_sa_mapped(self, obj):
        try:
            class_mapper(type(obj))
            return True
        except:
            return False


class ProblematicValueError(Exception):

    def __init__(self, value, message):
        self.value = value
        self.message = message


    def __str__(self):
        return repr(self.message)


class Conversation:

    def __init__(self, end_handler = None):
        # Callbacks
        self.end = end_handler
        self.resume = None
        self.next_text = None
        self.next_photo = None

        # Conversation Context
        self.ctxt = Context()

        # Command Handling
        self._overrides = []


    def clean_overrides(self):
        self._overrides = []


    def has_overrides(self):
        return len(self._overrides) > 0


    def override_with(self, options):
        flat_options = [option for row in options for option in row]
        self._overrides = flat_options


    def override_for(self, callback = None, text = None, name = None, module = None):
        if callback:
            for override in self._overrides:
                if override[1] == callback:
                    return override

        if text:
            for override in self._overrides:
                if override[0] == text:
                    return override

        if name:
            for override in self._overrides:
                if override[1].__name__ == name:
                    if module:
                        if override[1].__module__ == module:
                            return override
                    else:
                        return override

        return None


    def clean_next(self):
        self.next_text = None
        self.next_photo = None
        self.whitelist_options = None


class ConversationStack:

    def __init__(self):
        self._conversations = []


    def start(self, conversation):
        self._conversations.append(conversation)


    def end(self, model, ctxt, chat, args):
        conversation = self._conversations.pop()
        chat.clean_options()

        if conversation.end:
            conversation.end(model, ctxt, chat, args)

        # Keep the last conversation.
        if not self._conversations:
            self.start(conversation)

        previous = self.current()
        if previous.resume:
            previous.resume(model, ctxt, chat, args)


    def current(self):
        return self._conversations[-1]


    def hard_reset(self):
        if len(self._conversations) > 1:
            self._conversations = [self._conversations[0]]
