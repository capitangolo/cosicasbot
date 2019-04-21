#!/usr/bin/env python
# -*- coding: utf-8 -*-

import enum
from sqlalchemy import Column, ForeignKey, Boolean, Unicode, Enum, Numeric, Text
from sqlalchemy.dialects.mysql import INTEGER, BIGINT
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class UserGroup(Base):
    __tablename__ = 'user_group'

    id = Column(INTEGER(unsigned=True), primary_key=True)
    name = Column(Unicode(50), unique=True)

    auto_group_list = Column(Text)
    payload = Column(Text)

    users = relationship('User', secondary='role')
    roles = relationship('Role')

    #TODO: Automatic groups.
    # Load automatic groups to memory
    # Delete roles from automatic groups
    # Create new roles on db.
    #
    # Update db roles on:
    # - Role added
    # - Role modified
    # - Role deleted


class User(Base):
    __tablename__ = 'user'

    id = Column(INTEGER(unsigned=True), primary_key=True)
    telegram_id = Column(BIGINT(unsigned=True), unique=True)
    telegram_handle = Column(Unicode(32), unique=True)
    name = Column(Unicode(20))
    lastname = Column(Unicode(50))
    vat_id = Column(Unicode(20), unique=True)
    invoice_address = Column(Unicode(250))
    shipping_address = Column(Unicode(250))
    email_address = Column(Unicode(50))
    phone_number = Column(Unicode(20))

    groups = relationship('UserGroup', secondary='role')
    roles = relationship('Role')

    cartitems = relationship('CartItem')
    orders = relationship('Order')


    def catalogs(self, conn):
        query = conn.query(Catalog)
        query = query.join(Catalog.group)
        query = query.join(UserGroup.roles)
        query = query.filter_by(user_ref=self.id)
        return query.all()


    def role_in(self, conn, user_role, group_id):
        query = conn.query(Role)
        query = query.filter_by(user_ref=self.id)
        query = query.filter_by(group_ref=group_id)
        query = query.filter_by(role=user_role)
        return query.first()


    @classmethod
    def default_user(cls):
        return User()


    @classmethod
    def by_id(cls, conn, user_id):
        return conn.query(User).get(user_id)


    @classmethod
    def by_telegram_id(cls, conn, user_id):
        query = conn.query(User).filter_by(telegram_id=user_id)
        return query.first()


    @classmethod
    def by_telegram_handle(cls, conn, handle):
        query = conn.query(User).filter_by(telegram_handle=handle)
        return query.first()


class RoleLevel(enum.Enum):
    user = 1
    moderator = 2
    admin = 3


class Role(Base):
    __tablename__ = 'role'

    user_ref = Column(INTEGER(unsigned=True), ForeignKey('user.id'), primary_key=True)
    group_ref = Column(INTEGER(unsigned=True), ForeignKey('user_group.id'), primary_key=True)
    role = Column(Enum(RoleLevel), default=RoleLevel.user)

    user = relationship('User')
    group = relationship('UserGroup')


class Catalog(Base):
    __tablename__ = 'catalog'

    id = Column(INTEGER(unsigned=True), primary_key=True)
    name = Column(Unicode(255), nullable=False, default='')
    group_ref = Column(INTEGER(unsigned=True), ForeignKey('user_group.id'), primary_key=True)

    products = relationship('Product')
    group = relationship('UserGroup', uselist=False)


class Product(Base):
    __tablename__ = 'product'

    id = Column(INTEGER(unsigned=True), primary_key=True)
    catalog_ref = Column(INTEGER(unsigned=True), ForeignKey('catalog.id'))
    name = Column(Unicode(255), nullable=False, default='')
    price = Column(Numeric(precision=10, scale=2), nullable=False, default=0)
    tax = Column(Numeric(precision=10, scale=2), nullable=False, default=0)

    detail = Column(Unicode(255), nullable=False, default='')

    catalog = relationship('Catalog', uselist=False)


class OrderStatus(enum.Enum):
    received = 1
    accepted = 2
    need_info = 3
    invoiced = 4
    paid = 5
    procesing = 6
    shipped = 7


class Order(Base):
    __tablename__ = 'order'

    id = Column(INTEGER(unsigned=True), primary_key=True)
    user_ref = Column(INTEGER(unsigned=True), ForeignKey('user.id'), nullable=False)
    status = Column(Enum(OrderStatus), default=OrderStatus.received)

    shipping_price = Column(Numeric(precision=10, scale=2), nullable=False, default=0)
    shipping_tax = Column(Numeric(precision=10, scale=2), nullable=False, default=0)

    customer_notes = Column(Unicode(255), nullable=False, default='')
    status_notes = Column(Unicode(255), nullable=False, default='')
    invoice_to = Column(Unicode(255), nullable=False, default='')
    ship_to = Column(Unicode(255), nullable=False, default='')


    user = relationship('User', uselist=False)

    # TODO: get values from config
    @classmethod
    def __shipping_price(cls, subtotal):
        if subtotal >= 30:
            return 0
        elif subtotal >=15:
            return 2.48
        else:
            return 4.96

    # TODO: update to use lineitems
    def subtotal(self):
        return self.keychain_price() + self.figurine7_price() + self.figurine10_price() + self.coin_price() + float(self.extras_price)


    def shipping_price(self):
        subtotal = self.subtotal()
        return self.__shipping_price(subtotal)


    def total(self):
        subtotal = self.subtotal()
        shipping =  self.__shipping_price(subtotal)
        return subtotal + shipping


class LineItems(Base):
    __tablename__ = 'lineitems'

    order_ref = Column(INTEGER(unsigned=True), ForeignKey('order.id'), nullable=False, primary_key=True)
    product_ref = Column(INTEGER(unsigned=True), ForeignKey('product.id'), nullable=False, primary_key=True)
    price = Column(Numeric(precision=10, scale=2), nullable=False, default=0)
    tax = Column(Numeric(precision=10, scale=2), nullable=False, default=0)
    quantity = Column(INTEGER(unsigned=True), nullable=False, default=1)

    notes = Column(Unicode(255), nullable=False, default='')

    order = relationship('Order', uselist=False)
    product = relationship('Product', uselist=False)


class CartItem(Base):
    __tablename__ = 'cartitem'

    user_ref = Column(INTEGER(unsigned=True), ForeignKey('user.id'), nullable=False, primary_key=True)
    product_ref = Column(INTEGER(unsigned=True), ForeignKey('product.id'), nullable=False, primary_key=True)
    quantity = Column(INTEGER(unsigned=True), nullable=False, default=1)

    user = relationship('User', uselist=False)
    product = relationship('Product', uselist=False)

class Discount(Base):
    __tablename__ = 'discount'

    id = Column(INTEGER(unsigned=True), primary_key=True)

    product_ref = Column(INTEGER(unsigned=True), index=True)
    catalog_ref = Column(INTEGER(unsigned=True), index=True)
    group_ref = Column(INTEGER(unsigned=True), index=True)
    user_ref = Column(INTEGER(unsigned=True), index=True)

    discount_price = Column(Numeric(precision=10, scale=2), default=0)
    discount_percent = Column(Numeric(precision=10, scale=2), default=0)



