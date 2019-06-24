#!/usr/bin/env python
# -*- coding: utf-8 -*-

import csv
from ..model.entities import *
from functools import partial
import io
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackQueryHandler, Filters
from telegram import MessageEntity, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton, TelegramError
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

        text = update.message.text
        args = text.split(' ', 1)[-1]

        chat = TelegramChat(ctxt, bot, self.m, update)
        self.bot.handle_command(ctxt, chat, callback, args)


    def __handle_text(self, bot, update):
        ctxt = self.__ctxt_for(update.effective_user.id, update.effective_user.username)

        text = update.message.text
        chat = TelegramChat(ctxt, bot, self.m, update)
        self.bot.handle_text(ctxt, chat, text)


    def __handle_photo(self, bot, update):
        ctxt = self.__ctxt_for(update.effective_user.id, update.effective_user.username)

        photo = update.message.photo
        chat = TelegramChat(ctxt, bot, self.m, update)
        self.bot.handle_photo(ctxt, chat, photo)


    def __handle_callback(self, bot, update):
        ctxt = self.__ctxt_for(update.effective_user.id, update.effective_user.username)

        text = update.callback_query.data
        chat = TelegramChat(ctxt, bot, self.m, update)
        self.bot.handle_inline(ctxt, chat, text)


    def __ctxt_for(self, telegram_user_id, telegram_user_name):
        user_id = self.__user_id_for(telegram_user_id, telegram_user_name)
        if user_id:
            ctxt = self.m.ctxt(user_id)
            return ctxt
        else:
            return self.m.visitor_ctxt('telegram', telegram_user_id)


    def __user_id_for(self, user_t_id, user_t_name):
        user_id = None

        db = self.m.db()
        user = User.by_telegram_id(db, user_t_id)

        # Legacy to support first users registered.
        # Will be removed soon
        if not user:
            user = User.by_telegram_handle(db, '@' + user_t_name)
            if user:
                user.telegram_id = user_t_id
                db.commit()
        # end Legacy

        if user:
            user_id = user.id

        db.close()
        return user_id


class TelegramChat:

    def __init__(self, ctxt, bot, model, update):
        self.ctxt = ctxt
        self.bot = bot
        self.update = update
        self.model = model
        self.clean = False


    def format(self):
        return 'txt'


    def user_id(self):
        return self.update.effective_user.id


    def username(self):
        return '@' + self.update.effective_user.username


    def screen_username(self, user):
        return user.telegram_handle


    def screen_command(self, command):
        return '/' + command


    def user_detail(self):
        user_id = 'unknown user'
        if self.ctxt.has_key('user_id'):
            user_id = self.ctxt.user_id
        elif self.ctxt.has_key('visitor_id'):
            user_id = self.ctxt.visitor_id
        return 'User: {} via Telegram: {} #{}'.format(user_id, self.username(), self.user_id())


    def replyText(self, text, reply_options=None, inline_args=None):
        keyboard, reply_markup = self._keyboard_for(reply_options, inline_args)

        if keyboard:
            conversation = self.ctxt.conversations.current()
            conversation.override_with(reply_options)

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
        i = 0
        for row in options:
            new_row = []
            for option in row:
                conversation = option[1].__module__
                command = option[1].__name__

                data = "{} {}".format(conversation, command)
                if inline_args is not None and len(inline_args) > 0:
                    data += ' ' + ' '.join(inline_args[i])

                button = InlineKeyboardButton(text=option[0], callback_data=data)
                new_row.append(button)
                i += 1
            keyboard.append(new_row)
        return keyboard


    def _keyboard_for(self, reply_options, inline_args=None):
        keyboard = None
        reply_markup = ReplyKeyboardRemove()

        if inline_args != None:
            keyboard = self.__convert_inline_keyboard(reply_options, inline_args)
            reply_markup=InlineKeyboardMarkup(keyboard)

        elif reply_options != None:
            keyboard = self.__convert_reply_keyboard(reply_options)
            reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)

        return keyboard, reply_markup


    def render(self, template_name, **kwargs):
        return self.model.render(template_name, self.format(), **kwargs)


    def replyTemplate(self, template_name, reply_options=None, inline_args=None, **kwargs):
        text = self.render(template_name, **kwargs)
        self.replyText(text, reply_options, inline_args)


    def replyPhoto(self, photo_file_path, reply_options=None, inline_args=None):
        keyboard, reply_markup = self._keyboard_for(reply_options, inline_args)

        if keyboard:
            conversation = self.ctxt.conversations.current()
            conversation.override_with(reply_options)

        with open(photo_file_path, 'rb') as photo_file:
            self.update.effective_chat.send_photo(
                photo_file,
                reply_markup=reply_markup
            )


    def replyCSV(self, data, filename, reply_options=None, inline_args=None):
        csv_string = io.StringIO()
        csv_bytes = io.BytesIO()

        csv_writer = csv.writer(csv_string)
        csv_writer.writerows(data)

        csv_string.seek(0)
        csv_bytes.write(csv_string.read().encode('utf-8'))

        csv_bytes.seek(0)

        self.replyDocument(csv_bytes, filename, reply_options, inline_args)

        csv_string.close()
        csv_bytes.close()


    def replyDocument(self, fileob, filename, reply_options=None, inline_args=None):
        keyboard, reply_markup = self._keyboard_for(reply_options, inline_args)

        if keyboard:
            conversation = self.ctxt.conversations.current()
            conversation.override_with(reply_options)

        fileob.seek(0)
        self.update.effective_chat.send_document(
            fileob,
            filename=filename,
            reply_markup=reply_markup
        )


    def callback_for_input(self, reply_options, input):
        for row in reply_options:
            for option in row:
                if option[0].lower() == input.strip().lower():
                    return option[1]
        return None


    def clean_options(self):
        if self.clean:
            return

        if not self.update.callback_query:
            return

        try:
            self.update.callback_query.edit_message_reply_markup(reply_markup=None)
            self.clean = True
        except TelegramError:
            self.model.log.warning('Error updating message: clean_options.')


    def update_options(self, reply_options, inline_args):
        keyboard = self.__convert_inline_keyboard(reply_options, inline_args)
        reply_markup=InlineKeyboardMarkup(keyboard)

        conversation = self.ctxt.conversations.current()
        conversation.override_with(reply_options)

        self.update.callback_query.edit_message_reply_markup(
            reply_markup=reply_markup
        )


    # ========
    # Entities
    # ========
    def fill_user(self, user):
        user.telegram_id = self.user_id()
        user.telegram_handle = self.username()
