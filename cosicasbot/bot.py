#!/usr/bin/env python
# -*- coding: utf-8 -*-
import threading

class Bot:


    def __init__(self, model):
        self.m = model

        self.interfaces = []

        self.sessions = {}


    def load_interfaces(self, interface_classes):
        for interface_cls in interface_classes:
            if interface_cls.can_load(self.m):
                interface = interface_cls(self.m, self.handle_text, self.handle_photo)
                self.register_interface(interface)


    def register_interface(self, interface):
        self.m.log.info('Registering interface: {}'.format(type(interface).__name__))
        self.interfaces.append(interface)


    def load_conversations(self, conversations):
        for conversation in conversations:
            self.register_conversation(conversation)


    def register_conversation(self, conversation):
        self.m.log.info('Registering conversation: {}'.format(conversation.__name__))

        for command in conversation._commands():
            self.register_command(command)


    def register_command(self, command):
        self.m.log.info('Registering command: {}'.format(command.__name__))
        for interface in self.interfaces:
            interface.register_command(command.__name__, command)


    def start(self):
        self.m.log.info('Starting interfaces.')
        for interface in self.interfaces:
            self.m.log.info('Starting: {}'.format(type(interface).__name__))
            thread = threading.Thread(target=interface.start)
            thread.start()


    def session_for(self, user_id):
        if user_id not in self.sessions:
            self.sessions[user_id] = {}

        return self.sessions[user_id]


    def handle_text(self, model, ctxt, chat, text):
        if ctxt.next_text:
            ctxt.next_text(model, ctxt, chat, text)


    def handle_photo(self):
        if ctxt.next_photo:
            ctxt.next_photo(model, ctxt, chat, text)

