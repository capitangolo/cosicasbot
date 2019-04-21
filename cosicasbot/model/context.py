#!/usr/bin/env python
# -*- coding: utf-8 -*-

from sqlalchemy.orm.util import class_mapper


class UserContexts:


    def __init__(self, user_id_property):
        self.user_id_property = user_id_property
        self.contexts = {}


    def context_for(self, user_id):
        if user_id not in self.contexts:
            self.contexts[user_id] = Context()
            setattr(self.contexts[user_id], self.user_id_property, user_id)
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

    def getData(self):
        return self.__dict__['__data']


    def whitelist(self, options):
        flat_options = [option for row in options for option in row]
        self.whitelist_options = flat_options


    def clean_next(self):
        self.next_text = None
        self.next_photo = None
        self.whitelist_options = None


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
