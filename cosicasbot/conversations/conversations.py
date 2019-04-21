#!/usr/bin/env python
# -*- coding: utf-8 -*-

from functools import partial
from jinja2 import Environment, FileSystemLoader
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Chat
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .entities import *

MAIN_ORG = 1


class CallbackManager:


    def __init__(self, config):
        self.config = config
        self.engine = create_engine(config.dbconnection)
        self.sessionmaker = sessionmaker(bind=self.engine)
        self.__init_template()


    def __init_template(self):
        self.templates_env = Environment(
            loader=FileSystemLoader(self.config.templates_path)
        )


    def callback_for(self, handler_conf):
        callback_name = handler_conf['callback']
        callback = getattr(self, callback_name)
        return partial(callback, handler_conf=handler_conf)

    def template(self, bot, update, handler_conf):
        template_name = handler_conf['template']
        reply = handler_conf['reply']
        private = handler_conf['private']
        template = self.templates_env.get_template(template_name)
        message = template.render(bot=bot, update=update, conf=handler_conf)
        if private:
            update.effective_user.send_message(message)
        elif reply:
            update.message.reply_text(message)
        else:
            update.effective_chat.send_message(message)

# -----------
# Admin stuff
# -----------

    def a_list_all_users(self, bot, update, handler_conf):
        session = self.sessionmaker()
        if not protect_role(session, RoleLevel.admin, MAIN_ORG, bot, update):
            return

        message = "User List:\n"

        organisations = session.query(Organisation).all()

        for organisation in organisations:
            message += "#{} {}\n".format(organisation.id, organisation.name)
            for user in organisation.users:
                admin_flag = " (admin)" if user.role_in(session, RoleLevel.admin, organisation.id) else ""
                moderator_flag = " (moderator)" if user.role_in(session, RoleLevel.moderator, organisation.id) else ""
                message += "- #{} {}{}{}\n".format(user.id, user.telegram_handle, admin_flag, moderator_flag)
            message += "\n"
        session.close()

        update.effective_user.send_message(message)

# ----
# Util
# ----

def protect_role(session, role, organisation_id, bot, update):
    user = user_from_update(session, update)
    user_role = user.role_in(session, role, organisation_id)
    if user_role:
        return True
    else:
        message = "You don't have permissions to run that command."
        update.effective_user.send_message(message)
        return False


def user_from_update(session, update):
    telegram_user = update.effective_user.name

    query = session.query(User)
    query = query.filter_by(telegram_handle=telegram_user)
    user = query.first()
    return user


# ---------------
# User management
# ---------------

class SignupCallbackManager:

    def __init__(self, engine):
        self.sessionmaker = sessionmaker(bind=engine)

# -- User signup
    SIGNUP_SHALL_CHANGE_NAME, SIGNUP_SET_NAME, SIGNUP_SHALL_CHANGE_LASTNAME, SIGNUP_SET_LASTNAME, SIGNUP_SHALL_CHANGE_INVOICE_ADDR, SIGNUP_SET_INVOICE_ADDR, SIGNUP_SHALL_CHANGE_INVOICE_VAT, SIGNUP_SET_INVOICE_VAT, SIGNUP_SHALL_CHANGE_SHIPPING_ADDR, SIGNUP_SET_SHIPPING_ADDR, SIGNUP_SHALL_CHANGE_EMAIL, SIGNUP_SET_EMAIL, SIGNUP_SHALL_CHANGE_PHONE, SIGNUP_SET_PHONE = range(14)

    SIGNUP_CHANGE_KEYBOARD = [['Cambiar', 'Mantener']]

    def signup_start(self, bot, update):
        if update.message.chat.type != Chat.PRIVATE:
            return ConversationHandler.END

        session = self.sessionmaker()
        user = user_from_update(session, update)

        if not user:
            message = "¡Hola {}!\n En estos momentos el registro de usuarios nuevos no está disponible, ¡vuelve pronto!".format(update.effective_user.name)
            update.message.reply_text(message, reply_markup=ReplyKeyboardRemove())
            return ConversationHandler.END

        message = "¡Hola {}!\n\nVamos a revisar tus datos. Si tienes algún problema puedes contactar con @CosicasCo.\n\n".format(user.telegram_handle)

        if user.name:
            message += "Me consta que tu nombre es: \n\n{}\n\n ¿Quieres cambiarlo?".format(user.name)
            update.message.reply_text(message,
                reply_markup=ReplyKeyboardMarkup(self.SIGNUP_CHANGE_KEYBOARD, one_time_keyboard=True, selective=True))
            return self.SIGNUP_SHALL_CHANGE_NAME
        else:
            return self.signup_ask_name(bot, update, message)


    def signup_shall_change_name(self, bot, update):
        if update.message.chat.type != Chat.PRIVATE:
            return ConversationHandler.END

        response = update.message.text
        if response == self.SIGNUP_CHANGE_KEYBOARD[0][0]:
            return self.signup_ask_name(bot, update, '')
        else:
            return self.signup_lastname(bot, update, '')


    def signup_ask_name(self, bot, update, message):
        if update.message.chat.type != Chat.PRIVATE:
            return ConversationHandler.END

        message += "¿Cuál es tu nombre de pila?"
        update.message.reply_text(message)
        return self.SIGNUP_SET_NAME


    def signup_set_name(self, bot, update):
        if update.message.chat.type != Chat.PRIVATE:
            return ConversationHandler.END

        name = update.message.text

        session = self.sessionmaker()
        user = user_from_update(session, update)
        user.name = name
        session.commit()

        message = "Encantado de conocerte {}.\n\n".format(name)
        return self.signup_lastname(bot, update, message)


    def signup_lastname(self, bot, update, message):
        if update.message.chat.type != Chat.PRIVATE:
            return ConversationHandler.END

        session = self.sessionmaker()
        user = user_from_update(session, update)

        if user.lastname:
            message += "Me consta que tu apellido es: \n\n{}\n\n ¿Quieres cambiarlo?".format(user.lastname)
            update.message.reply_text(message,
                reply_markup=ReplyKeyboardMarkup(self.SIGNUP_CHANGE_KEYBOARD, one_time_keyboard=True, selective=True))
            return self.SIGNUP_SHALL_CHANGE_LASTNAME
        else:
            return self.signup_ask_lastname(bot, update, message)


    def signup_shall_change_lastname(self, bot, update):
        if update.message.chat.type != Chat.PRIVATE:
            return ConversationHandler.END

        response = update.message.text
        if response == self.SIGNUP_CHANGE_KEYBOARD[0][0]:
            return self.signup_ask_lastname(bot, update, '')
        else:
            return self.signup_invoice_addr(bot, update, '')


    def signup_ask_lastname(self, bot, update, message):
        if update.message.chat.type != Chat.PRIVATE:
            return ConversationHandler.END

        message += "¿Cuál es tu apellido?"
        update.message.reply_text(message,
                                  reply_markup=ReplyKeyboardRemove())
        return self.SIGNUP_SET_LASTNAME


    def signup_set_lastname(self, bot, update):
        if update.message.chat.type != Chat.PRIVATE:
            return ConversationHandler.END

        response = update.message.text

        session = self.sessionmaker()
        user = user_from_update(session, update)
        user.lastname = response
        session.commit()

        message = 'Encantado de conocerte {} {}.\n\n'.format(user.name, user.lastname)

        return self.signup_invoice_addr(bot, update, message)


    def signup_invoice_addr(self, bot, update, message):
        if update.message.chat.type != Chat.PRIVATE:
            return ConversationHandler.END

        session = self.sessionmaker()
        user = user_from_update(session, update)

        if user.invoice_address:
            message += 'Me consta que tu dirección de facturación es: \n\n{}\n\n ¿Quieres cambiarla?'.format(user.invoice_address)
            update.message.reply_text(message,
                reply_markup=ReplyKeyboardMarkup(self.SIGNUP_CHANGE_KEYBOARD, one_time_keyboard=True, selective=True))
            return self.SIGNUP_SHALL_CHANGE_INVOICE_ADDR
        else:
            return self.signup_ask_invoice_addr(bot, update, message)


    def signup_shall_change_invoice_addr(self, bot, update):
        if update.message.chat.type != Chat.PRIVATE:
            return ConversationHandler.END

        response = update.message.text
        if response == self.SIGNUP_CHANGE_KEYBOARD[0][0]:
            return self.signup_ask_invoice_addr(bot, update, '')
        else:
            return self.signup_invoice_vat(bot, update, '')


    def signup_ask_invoice_addr(self, bot, update, message):
        if update.message.chat.type != Chat.PRIVATE:
            return ConversationHandler.END

        message += '¿Cuál es tu dirección de facturación?\n\nAcuérdate de incluir: Calle, Número, Piso y puerta, Código Postal, Población\n\n ¿Las facturas no van a tu nombre? Añade también a la atención de quién debemos emitir las facturas.'
        update.message.reply_text(message,
                                  reply_markup=ReplyKeyboardRemove())
        return self.SIGNUP_SET_INVOICE_ADDR


    def signup_set_invoice_addr(self, bot, update):
        if update.message.chat.type != Chat.PRIVATE:
            return ConversationHandler.END

        response = update.message.text

        session = self.sessionmaker()
        user = user_from_update(session, update)
        user.invoice_address = response
        user.shipping_address = response
        session.commit()

        message = "Guardo tu dirección de factuación:\n\n{}\n\n".format(user.invoice_address)

        return self.signup_invoice_vat(bot, update, message)


    def signup_invoice_vat(self, bot, update, message):
        if update.message.chat.type != Chat.PRIVATE:
            return ConversationHandler.END

        session = self.sessionmaker()
        user = user_from_update(session, update)

        if user.vat_id:
            message += 'Me consta que tu NIF es: \n\n{}\n\n ¿Quieres cambiarlo?'.format(user.vat_id)
            update.message.reply_text(message,
                reply_markup=ReplyKeyboardMarkup(self.SIGNUP_CHANGE_KEYBOARD, one_time_keyboard=True, selective=True))
            return self.SIGNUP_SHALL_CHANGE_INVOICE_VAT
        else:
            return self.signup_ask_invoice_vat(bot, update, message)


    def signup_shall_change_invoice_vat(self, bot, update):
        if update.message.chat.type != Chat.PRIVATE:
            return ConversationHandler.END

        response = update.message.text
        if response == self.SIGNUP_CHANGE_KEYBOARD[0][0]:
            return self.signup_ask_invoice_vat(bot, update, '')
        else:
            return self.signup_shipping_addr(bot, update, '')


    def signup_ask_invoice_vat(self, bot, update, message):
        if update.message.chat.type != Chat.PRIVATE:
            return ConversationHandler.END

        message += '¿Cuál es el Número de Identidad Fiscal al que debemos emitir las facturas? (NIF / CIF / DNI)'
        update.message.reply_text(message,
                                  reply_markup=ReplyKeyboardRemove())
        return self.SIGNUP_SET_INVOICE_VAT


    def signup_set_invoice_vat(self, bot, update):
        if update.message.chat.type != Chat.PRIVATE:
            return ConversationHandler.END

        response = update.message.text

        session = self.sessionmaker()
        user = user_from_update(session, update)
        user.vat_id = response
        session.commit()

        message = "Guardo tu NIF (8 números y letra sin espacios): {}\n\n".format(user.vat_id)

        return self.signup_shipping_addr(bot, update, message)


    def signup_shipping_addr(self, bot, update, message):
        if update.message.chat.type != Chat.PRIVATE:
            return ConversationHandler.END

        session = self.sessionmaker()
        user = user_from_update(session, update)

        if user.shipping_address:
            message += 'Me consta que tu dirección de envío es: \n\n{}\n\n ¿Quieres cambiarla?'.format(user.shipping_address)
            update.message.reply_text(message,
                reply_markup=ReplyKeyboardMarkup(self.SIGNUP_CHANGE_KEYBOARD, one_time_keyboard=True, selective=True))
            return self.SIGNUP_SHALL_CHANGE_SHIPPING_ADDR
        else:
            return self.signup_ask_shipping_addr(bot, update, message)


    def signup_shall_change_shipping_addr(self, bot, update):
        if update.message.chat.type != Chat.PRIVATE:
            return ConversationHandler.END

        response = update.message.text
        if response == self.SIGNUP_CHANGE_KEYBOARD[0][0]:
            return self.signup_ask_shipping_addr(bot, update, '')
        else:
            return self.signup_email(bot, update, '')


    def signup_ask_shipping_addr(self, bot, update, message):
        if update.message.chat.type != Chat.PRIVATE:
            return ConversationHandler.END

        message += '¿Cuál es tu dirección de envío? Acuérdate de incluir: Calle, Número, Piso y puerta, Código Postal, Ciudad'
        update.message.reply_text(message,
                                  reply_markup=ReplyKeyboardRemove())
        return self.SIGNUP_SET_SHIPPING_ADDR


    def signup_set_shipping_addr(self, bot, update):
        if update.message.chat.type != Chat.PRIVATE:
            return ConversationHandler.END

        response = update.message.text

        session = self.sessionmaker()
        user = user_from_update(session, update)
        user.shipping_address = response
        session.commit()

        message = "Guardo tu dirección de envío:\n\n{}\n\n".format(user.shipping_address)

        return self.signup_email(bot, update, message)


    def signup_email(self, bot, update, message):
        if update.message.chat.type != Chat.PRIVATE:
            return ConversationHandler.END

        session = self.sessionmaker()
        user = user_from_update(session, update)

        if user.email_address:
            message += 'Me consta que tu dirección email es: {}\n\n ¿Quieres cambiarlo?'.format(user.email_address)
            update.message.reply_text(message,
                reply_markup=ReplyKeyboardMarkup(self.SIGNUP_CHANGE_KEYBOARD, one_time_keyboard=True, selective=True))
            return self.SIGNUP_SHALL_CHANGE_EMAIL
        else:
            return self.signup_ask_email(bot, update, message)


    def signup_shall_change_email(self, bot, update):
        if update.message.chat.type != Chat.PRIVATE:
            return ConversationHandler.END

        response = update.message.text
        if response == self.SIGNUP_CHANGE_KEYBOARD[0][0]:
            return self.signup_ask_email(bot, update, '')
        else:
            return self.signup_phone(bot, update, '')


    def signup_ask_email(self, bot, update, message):
        if update.message.chat.type != Chat.PRIVATE:
            return ConversationHandler.END

        message += '¿Cuál es tu dirección de email?'
        update.message.reply_text(message,
                                  reply_markup=ReplyKeyboardRemove())
        return self.SIGNUP_SET_EMAIL


    def signup_set_email(self, bot, update):
        if update.message.chat.type != Chat.PRIVATE:
            return ConversationHandler.END

        response = update.message.text

        session = self.sessionmaker()
        user = user_from_update(session, update)
        user.email_address = response
        session.commit()

        message = "Guardo tu dirección email: {}\n\n".format(user.email_address)

        return self.signup_phone(bot, update, message)


    def signup_phone(self, bot, update, message):
        if update.message.chat.type != Chat.PRIVATE:
            return ConversationHandler.END

        session = self.sessionmaker()
        user = user_from_update(session, update)

        if user.phone_number:
            message += 'Me consta que tu teléfono es: {}\n\n ¿Quieres cambiarlo?'.format(user.phone_number)
            update.message.reply_text(message,
                reply_markup=ReplyKeyboardMarkup(self.SIGNUP_CHANGE_KEYBOARD, one_time_keyboard=True, selective=True))
            return self.SIGNUP_SHALL_CHANGE_PHONE
        else:
            return self.signup_ask_phone(bot, update, message)


    def signup_shall_change_phone(self, bot, update):
        if update.message.chat.type != Chat.PRIVATE:
            return ConversationHandler.END

        response = update.message.text
        if response == self.SIGNUP_CHANGE_KEYBOARD[0][0]:
            return self.signup_ask_phone(bot, update, '')
        else:
            return self.signup_finish(bot, update, '')


    def signup_ask_phone(self, bot, update, message):
        if update.message.chat.type != Chat.PRIVATE:
            return ConversationHandler.END

        message += '¿Cuál es tu número de teléfono?'
        update.message.reply_text(message,
                                  reply_markup=ReplyKeyboardRemove())
        return self.SIGNUP_SET_PHONE


    def signup_set_phone(self, bot, update):
        if update.message.chat.type != Chat.PRIVATE:
            return ConversationHandler.END

        response = update.message.text

        session = self.sessionmaker()
        user = user_from_update(session, update)
        user.phone_number = response
        session.commit()

        message = "Guardo tu número de teléfono: {}\n\n".format(user.phone_number)

        return self.signup_finish(bot, update, message)


    def signup_finish(self, bot, update, message):
        if update.message.chat.type != Chat.PRIVATE:
            return ConversationHandler.END

        update.message.reply_text('Perfecto, ya tengo todos tus datos. Cuando quieras puedes editarlos ejecutando /signup .',
                                  reply_markup=ReplyKeyboardRemove())

        return ConversationHandler.END


    def signup_cancel(self, bot, update):
        if update.message.chat.type != Chat.PRIVATE:
            return ConversationHandler.END

        update.message.reply_text('Perfecto, cuando quieras continuar el registro aquí estaré :).',
                                  reply_markup=ReplyKeyboardRemove())

        return ConversationHandler.END


# ---------------
# Order management
# ---------------

class TemporderCallbackManager:


    def __init__(self, config, engine):
        self.sessionmaker = sessionmaker(bind=engine)
        self.config = config
        self.templates_env = Environment(
            loader=FileSystemLoader(self.config.templates_path),
            line_statement_prefix='#',
            autoescape=False
        )


    def __init_user_tempoder(self, session, user):
        if not user:
            return False

        if not user.temporder:
            user.temporder = TempOrder.default_temporder()
            session.commit()

        return True


    def order_show(self, bot, update):
        session = self.sessionmaker()
        user = user_from_update(session, update)
        if not self.__init_user_tempoder(session, user):
            return None

        template_name = 'temporder_show.template'
        template = self.templates_env.get_template(template_name)

        message = template.render(bot=bot, update=update, temporder=user.temporder, user=user)
        update.effective_user.send_message(message)


    def order_help(self, bot, update):
        session = self.sessionmaker()
        user = user_from_update(session, update)
        if not self.__init_user_tempoder(session, user):
            return None

        template_name = 'temporder_help.template'
        template = self.templates_env.get_template(template_name)

        message = template.render(bot=bot, update=update, temporder=user.temporder, user=user)
        update.effective_user.send_message(message)


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


    def order_keychain(self, bot, update):
        return self.__order_item(bot, update, '/order_keychain', 'keychain_count', 'int')


    def order_figurine7(self, bot, update):
        return self.__order_item(bot, update, '/order_figurine7', 'figurine7_count', 'int')


    def order_figurine10(self, bot, update):
        return self.__order_item(bot, update, '/order_figurine10', 'figurine10_count', 'int')


    def order_coin(self, bot, update):
        return self.__order_item(bot, update, '/order_coin', 'coin_count', 'int')


    def order_extras(self, bot, update):
        return self.__order_item(bot, update, '/order_extras', 'extras_description', 'string')


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


