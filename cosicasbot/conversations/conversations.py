#!/usr/bin/env python
# -*- coding: utf-8 -*-

from functools import partial
from jinja2 import Environment, FileSystemLoader
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Chat
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .entities import *


# ---------------
# Order management
# ---------------

class TemporderCallbackManager:


    def order_confirm(self, bot, update):
        session = self.sessionmaker()
        user = user_from_update(session, update)
        if not self.__init_user_tempoder(session, user):
            return None

        user.temporder.confirmed = True
        user.temporder.status = 'confirmada, en breves te enviaremos la factura'
        session.commit()

        return self.order_show(bot, update)


    def __order_item(self, bot, update, command, item_key, value_type):
        session = self.sessionmaker()
        user = user_from_update(session, update)
        if not self.__init_user_tempoder(session, user):
            return None

        if user.temporder.confirmed:
            return None

        response = update.message.text
        try:
            param = response.replace(command,'').strip()
            value = 0
            if value_type == 'int':
                value = int(float(param))
            elif value_type == 'string':
                if not param:
                    raise ValueError('Empty value.')
                value = param

            setattr(user.temporder, item_key, value)
            session.commit()

            return self.order_show(bot, update)

        except:
            if value_type == 'int':
                item_quantity = getattr(user.temporder, item_key)
            elif value_type == 'string':
                item_quantity = 1
            item_name = user.temporder.name_for(item_key)
            item_price = user.temporder.price_for(item_key)

            template_name = 'temporder_line_item.template'
            template = self.templates_env.get_template(template_name)
            message = template.render(bot=bot, update=update, item_quantity=item_quantity, item_name=item_name, item_price=item_price, command=command)
            update.effective_user.send_message(message)


    def admin_list_orders(self, bot, update):
        session = self.sessionmaker()
        if not protect_role(session, RoleLevel.admin, MAIN_ORG, bot, update):
            return None

        orders = session.query(TempOrder).filter(TempOrder.status != 'cerrado')
        message = ''
        items = {
            'keychain': 0,
            'figurine7': 0,
            'figurine10': 0,
            'coin': 0,
            'extras': '\n'
        }
        for temporder in orders:
            short_status = temporder.status.split(',')[0]
            message += '#{} - {} - {}\n'.format(temporder.id, temporder.user.telegram_handle, short_status)

            items['keychain'] += temporder.keychain_count
            items['figurine7'] += temporder.figurine7_count
            items['figurine10'] += temporder.figurine10_count
            items['coin'] += temporder.coin_count
            items['extras'] += temporder.extras_description + '\n\n'

        message += '\nResumen:\n\n'
        for key, value in items.items():
            message += '{}: {}\n'.format(key, value)

        return update.effective_user.send_message(message)


    def admin_view_order_items(self, bot, update):
        session = self.sessionmaker()
        if not protect_role(session, RoleLevel.admin, MAIN_ORG, bot, update):
            return None

        response = update.message.text
        command = '/admin_view_order_items'
        param = response.replace(command,'').strip()
        value = int(float(param))

        temporder = session.query(TempOrder).filter_by(id = value).first()

        message = 'Pedido #{} de {}:\n\n'.format(temporder.id, temporder.user.telegram_handle)
        message += 'Llaveros: {}\n'.format(temporder.keychain_count)
        message += 'Figuras 7: {}\n'.format(temporder.figurine7_count)
        message += 'Figuras 10: {}\n'.format(temporder.figurine10_count)
        message += 'Monedas: {}\n'.format(temporder.coin_count)
        message += 'Extras: {}\n'.format(temporder.extras_description)
        return update.effective_user.send_message(message)


    def admin_view_order(self, bot, update):
        session = self.sessionmaker()
        if not protect_role(session, RoleLevel.admin, MAIN_ORG, bot, update):
            return None

        response = update.message.text
        command = '/admin_view_order'
        param = response.replace(command,'').strip()
        value = int(float(param))

        temporder = session.query(TempOrder).filter_by(id = value).first()

        message = 'Pedido #{} de {}:\n\n'.format(temporder.id, temporder.user.telegram_handle)
        message += 'Llaveros: {}\n'.format(temporder.keychain_count)
        message += 'Figuras 7: {}\n'.format(temporder.figurine7_count)
        message += 'Figuras 10: {}\n'.format(temporder.figurine10_count)
        message += 'Monedas: {}\n'.format(temporder.coin_count)
        message += 'Extras: {}\n'.format(temporder.extras_description)

        message += '\n-------\n\n'

        message += 'Subtotal: {}\n'.format(temporder.subtotal())
        message += 'Envío: {}\n'.format(temporder.shipping_price())
        message += 'Total sin IVA: {}\n'.format(temporder.total())
        message += 'Total con IVA: {}\n'.format(temporder.total() * 1.21)

        message += '\n-------\n\n'

        message += 'Estado: {}\n'.format(temporder.status)

        message += '\n-------\n\n'

        user = temporder.user
        message += 'Facturar a:\n{} {}\n{}\n{}\n{}\n\n'.format(
            user.name,
            user.lastname,
            user.vat_id,
            user.email_address,
            user.invoice_address
        )

        message += 'Enviar a:\n{} {}\n{}\n{}\n{}\n\n'.format(
            user.name,
            user.lastname,
            user.email_address,
            user.phone_number,
            user.shipping_address
        )

        return update.effective_user.send_message(message)


    def admin_order_open(self, bot, update):
        session = self.sessionmaker()
        if not protect_role(session, RoleLevel.admin, MAIN_ORG, bot, update):
            return None

        response = update.message.text
        try:
            command = '/admin_order_open'
            param = response.replace(command,'').strip()
            value = int(float(param))

            temporder = session.query(TempOrder).filter_by(id = value).first()
            temporder.status = 'sin confirmar'
            temporder.confirmed = False
            session.commit()

            message = "Pedido {} abierto".format(value)
            return update.effective_user.send_message(message)

        except:
            message = "Error abriendo el pedido"
            return update.effective_user.send_message(message)


