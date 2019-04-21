#!/usr/bin/env python
# -*- coding: utf-8 -*-
import threading

class Bot:


    def __init__(self, model):
        self.m = model

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
        # Don't execute commands when we are expecting a text or a photo
        # Allow, howhever to execute whitelisted options.
        if self.__expecting_response(ctxt) and ctxt.whitelist_options:
            blocked = True
            for option in ctxt.whitelist_options:
                if option[1] == callback:
                    blocked = False
                    break
            if blocked:
                return
        callback(self.m, ctxt, chat, args)


    def handle_text(self, ctxt, chat, text):
        # Process only if we are expecting it
        if not ctxt.next_text:
            return

        # If it's a whitelisted option,
        # execute the option instead of processing the text
        if ctxt.whitelist_options:
            for option in ctxt.whitelist_options:
                if option[0] == text:
                    option[1](self.m, ctxt, chat, text)
                    return

        ctxt.next_text(self.m, ctxt, chat, text)


    def handle_photo(self, ctxt, chat, photo):
        # Process only if we are expecting it
        if not ctxt.next_photo:
            return

        ctxt.next_photo(self.m, ctxt, chat, photo)


    def handle_inline(self, ctxt, chat, text):
        parts = text.split(' ', 2)
        conversation_name = parts[0]
        command_name = parts[1]
        args = None
        if len(parts) > 2:
            args = parts[2]

        if conversation_name not in self.conversations:
            return

        conversation = self.conversations[conversation_name]
        commands = conversation['commands']

        for command in commands:
            if command.__name__ == command_name:
                self.handle_command(ctxt, chat, command, args)
                return


    def __expecting_response(self, ctxt):
        return ctxt.next_text or ctxt.next_photo
