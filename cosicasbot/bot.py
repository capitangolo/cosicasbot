#!/usr/bin/env python
# -*- coding: utf-8 -*-
import threading

class Bot:


    def __init__(self, model, start):
        self.m = model

        self.start_callback = start

        self.interfaces = []

        self.conversations = {}


    def load_interfaces(self, interface_classes):
        for interface_cls in interface_classes:
            if interface_cls.can_load(self.m):
                interface = interface_cls(self)
                self.register_interface(interface)


    def register_interface(self, interface):
        self.m.log.info('Registering interface: {}'.format(type(interface).__name__))
        self.interfaces.append(interface)


    def load_conversations(self, conversations):
        for conversation in conversations:
            self.register_conversation(conversation)


    def register_conversation(self, conversation):
        self.m.log.info('Registering conversation: {}'.format(conversation.__name__))

        self.conversations[conversation.__name__] = {
            'commands': conversation._commands()
        }

        for command in conversation._commands():
            self.register_command(command)


    def register_command(self, command):
        # TODO: Check for duplicates
        self.m.log.info('Registering command: {}'.format(command.__name__))
        for interface in self.interfaces:
            interface.register_command(command.__name__, command)


    def start(self):
        self.m.log.info('Starting interfaces.')
        for interface in self.interfaces:
            self.m.log.info('Starting: {}'.format(type(interface).__name__))
            thread = threading.Thread(target=interface.start)
            thread.start()


    def handle_command(self, ctxt, chat, callback, args):
        conversation = ctxt.conversations.current()

        # Don't execute commands when we are expecting a text or a photo
        # Allow, howhever to execute whitelisted options.
        if self.__expecting_response(conversation):
            override = conversation.override_for(callback = callback)

            if not override and callback != self.start_callback:
                return

        callback(self.m, ctxt, chat, args)


    def handle_text(self, ctxt, chat, text):
        conversation = ctxt.conversations.current()

        # Process only if we are expecting it
        if not conversation or not conversation.next_text:
            return

        # If it's a whitelisted option,
        # execute the option instead of processing the text
        override = conversation.override_for(text = text)

        if override:
            override[1](self.m, ctxt, chat, text)
            return

        conversation.next_text(self.m, ctxt, chat, text)


    def handle_photo(self, ctxt, chat, photo):
        conversation = ctxt.conversations.current()

        # Process only if we are expecting it
        if not conversation or not conversation.next_photo:
            return

        conversation.next_photo(self.m, ctxt, chat, photo)


    def handle_inline(self, ctxt, chat, text):
        conversation = ctxt.conversations.current()

        parts = text.split(' ', 2)
        conversation_name = parts[0]
        command_name = parts[1]
        args = None
        if len(parts) > 2:
            args = parts[2]

        override = conversation.override_for(name = command_name, module = conversation_name)

        if override:
            override[1](self.m, ctxt, chat, args)


    def __expecting_response(self, conversation):
        return conversation.has_overrides() or conversation.next_text or conversation.next_photo
