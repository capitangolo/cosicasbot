#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
from cosicasbot import config, callbacks
import logging
import re
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler
from telegram import MessageEntity
import unicodedata


VERSION = '1.0.6'

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'config_file'
        , help="Config file to read bot config."
    )
    return parser.parse_args()


def error(bot, update, error):
    logger.warning('Update "%s" caused error "%s"', update, error)

# --- Handlers

def create_signup_handler(dbengine):
    cm = callbacks.SignupCallbackManager(dbengine)
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('signup', cm.signup_start)],

        states={
            cm.SIGNUP_SHALL_CHANGE_NAME: [MessageHandler(Filters.text, cm.signup_shall_change_name)],
            cm.SIGNUP_SET_NAME: [MessageHandler(Filters.text, cm.signup_set_name)],
            cm.SIGNUP_SHALL_CHANGE_LASTNAME: [MessageHandler(Filters.text, cm.signup_shall_change_lastname)],
            cm.SIGNUP_SET_LASTNAME: [MessageHandler(Filters.text, cm.signup_set_lastname)],
            cm.SIGNUP_SHALL_CHANGE_INVOICE_ADDR: [MessageHandler(Filters.text, cm.signup_shall_change_invoice_addr)],
            cm.SIGNUP_SET_INVOICE_ADDR: [MessageHandler(Filters.text, cm.signup_set_invoice_addr)],
            cm.SIGNUP_SHALL_CHANGE_INVOICE_VAT: [MessageHandler(Filters.text, cm.signup_shall_change_invoice_vat)],
            cm.SIGNUP_SET_INVOICE_VAT: [MessageHandler(Filters.text, cm.signup_set_invoice_vat)],
            cm.SIGNUP_SHALL_CHANGE_SHIPPING_ADDR: [MessageHandler(Filters.text, cm.signup_shall_change_shipping_addr)],
            cm.SIGNUP_SET_SHIPPING_ADDR: [MessageHandler(Filters.text, cm.signup_set_shipping_addr)],
            cm.SIGNUP_SHALL_CHANGE_EMAIL: [MessageHandler(Filters.text, cm.signup_shall_change_email)],
            cm.SIGNUP_SET_EMAIL: [MessageHandler(Filters.text, cm.signup_set_email)],
            cm.SIGNUP_SHALL_CHANGE_PHONE: [MessageHandler(Filters.text, cm.signup_shall_change_phone)],
            cm.SIGNUP_SET_PHONE: [MessageHandler(Filters.text, cm.signup_set_phone)]
        },

        fallbacks=[CommandHandler('signup_cancel', cm.signup_cancel)]
    )
    return conv_handler

def register_temporder_callbacks(config, dbengine, dp):
    to = callbacks.TemporderCallbackManager(config, dbengine)
    commands = [
        'order_show',
        'order_help',
        'order_confirm',
        'order_keychain',
        'order_figurine7',
        'order_figurine10',
        'order_coin',
        'order_extras',

        'admin_list_orders',
        'admin_view_order_items',
        'admin_view_order',
        'admin_order_open'
    ]

    for command in commands:
        register_temporder_callback(dp, to, command)


def register_temporder_callback(dispatcher, manager, command):
    dispatcher.add_handler(CommandHandler(command, getattr(manager, command)))



# --- Main

def main():
    args = parse_args()
    cfg = config.Config(args.credentials_file, args.config_file)

    logger.info('Starting cosicasbot v{} for {}'.format(VERSION, cfg.botname))

    updater = Updater(cfg.apikey)

    dp = updater.dispatcher
    for handler in cfg.handlers:
        dp.add_handler(handler)

    dp.add_handler(create_signup_handler(cfg.callback_manager.engine))

    register_temporder_callbacks(cfg, cfg.callback_manager.engine, dp)

    dp.add_error_handler(error)

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()

