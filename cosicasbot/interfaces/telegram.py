#!/usr/bin/env python
# -*- coding: utf-8 -*-

from ..model.entities import *
from functools import partial
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackQueryHandler, Filters
from telegram import MessageEntity, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton
import unicodedata


class Telegram:


    @classmethod
    def can_load(cls, model):
        return model.cfg.telegram_apikey


    def __init__(self, bot):
        self.bot = bot
        self.m = bot.m

        self.updater = Updater(self.m.cfg.telegram_apikey)
        self.dp = self.updater.dispatcher

        self.__register_handlers(self.dp)


    def start(self):
        self.updater.start_polling()


    def __register_handlers(self, dp):
        text_handler = MessageHandler(Filters.text & Filters.private, self.__handle_text)
        photo_handler = MessageHandler(Filters.photo & Filters.private, self.__handle_photo)
        callback_handler = CallbackQueryHandler( self.__handle_callback )

        dp.add_handler(text_handler)
        dp.add_handler(photo_handler)
        dp.add_handler(callback_handler)
        dp.add_error_handler(self.error)


    def error(self, bot, update, error):
        self.m.log.warning('Update "%s" caused error "%s"', update, error)


    def register_command(self, name, callback):
        command_callback = partial(self.__handle_command, callback=callback)
        command_handler = CommandHandler(name, command_callback)
        self.dp.add_handler(command_handler)


    def __handle_command(self, bot, update, callback):
        ctxt = self.__ctxt_for(update.effective_user.id, update.effective_user.username)

        if ctxt.next_text or ctxt.next_photo:
            return

        text = update.message.text
        args = text.split(' ', 1)[-1]

        chat = TelegramChat(bot, self.m, update)
        callback(self.m, ctxt, chat, args)


    def __handle_text(self, bot, update, text=None):
        ctxt = self.__ctxt_for(update.effective_user.id, update.effective_user.username)

        if ctxt.next_photo:
            return

        if not text:
            text = update.message.text
        chat = TelegramChat(bot, self.m, update)
        self.bot.handle_text(self.m, ctxt, chat, text)


    def __handle_photo(self, bot, update):
        ctxt = self.__ctxt_for(update.effective_user.id, update.effective_user.username)

        if ctxt.next_text:
            return

        photo = update.message.photo
        chat = TelegramChat(bot, self.m, update)
        self.bot.handle_photo(self.m, ctxt, chat, photo)


    def __handle_callback(self, bot, update):
        ctxt = self.__ctxt_for(update.effective_user.id, update.effective_user.username)

        text = update.callback_query.data
        chat = TelegramChat(bot, self.m, update)
        self.bot.handle_inline(bot, ctxt, chat, text)


    def __ctxt_for(self, telegram_user_id, telegram_user_name):
        user = self.__user_for(telegram_user_id, telegram_user_name)
        if user:
            ctxt = self.m.ctxt(user.id)
            ctxt.user = user
            return ctxt
        else:
            return self.m.visitor_ctxt('telegram', telegram_user_id)


    def __user_for(self, user_id, user_name):
        db = self.m.db()
        user = User.user_by_telegram_id(db, user_id)

        # Legacy to support first users registered.
        # Will be removed soon
        if not user:
            user = User.user_by_telegram_handle(db, '@' + user_name)
            if user:
                user.telegram_id = user_id
                db.commit()
                id = user.id
        # end Legacy

        db.close()

        return user


class TelegramChat:

    def __init__(self, bot, model, update):
        self.bot = bot
        self.update = update
        self.model = model


    def format(self):
        return 'txt'


    def username(self):
        return '@' + self.update.effective_user.username


    def screen_username(self, user):
        return user.telegram_handle


    def screen_command(self, command):
        return '/' + command


    def replyText(self, text, reply_options=None, inline_args=None):
        reply_markup = ReplyKeyboardRemove()

        if inline_args != None:
            keyboard = self.__convert_inline_keyboard(reply_options, inline_args)
            reply_markup=InlineKeyboardMarkup(keyboard)

        elif reply_options != None:
            keyboard = self.__convert_reply_keyboard(reply_options)
            reply_markup=ReplyKeyboardMarkup(keyboard)

        self.update.effective_chat.send_message(
            text,
            reply_markup=reply_markup
        )


    def __convert_reply_keyboard(self, options):
        keyboard = []
        for row in options:
            new_row = []
            for option in row:
                new_row.append(KeyboardButton(text=option[0]))
            keyboard.append(new_row)
        return keyboard

    def __convert_inline_keyboard(self, options, inline_args):
        keyboard = []
        for row in options:
            new_row = []
            for option in row:
                conversation = option[1].__module__
                command = option[1].__name__

                data = "{} {}".format(conversation, command)
                if inline_args:
                    data += ' ' + ' '.join(inline_args)

                button = InlineKeyboardButton(text=option[0], callback_data=data)
                new_row.append(button)
            keyboard.append(new_row)
        return keyboard


    def replyTemplate(self, template_name, reply_options=None, inline_args=None, **kwargs):
        text = self.model.render(template_name, self.format(), **kwargs)
        self.replyText(text, reply_options, inline_args)


    def callback_for_input(self, reply_options, input):
        for row in reply_options:
            for option in row:
                if option[0].lower() == input.strip().lower():
                    return option[1]
        return None
