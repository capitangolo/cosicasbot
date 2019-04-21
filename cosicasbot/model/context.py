#!/usr/bin/env python
# -*- coding: utf-8 -*-


class UserContexts:


    def __init__(self):
        self.contexts = {}


    def context_for(self, user_id):
        if user_id not in self.contexts:
            self.contexts[user_id] = Context()
        return self.contexts[user_id]


class Context:


    def __init__(self):
        self.__dict__['__data'] = {}


    def __getattr__(self, name):
        if name in self.__dict__['__data']:
            return self.__dict__['__data'][name]
        return None


    def __setattr__(self, name, value):
        self.__dict__['__data'][name] = value


    def __delattr__(self, name):
        if name in self.__dict__['__data']:
            del self.__dict__['__data'][obj]

    def getData(self):
        return self.__dict__['__data']
