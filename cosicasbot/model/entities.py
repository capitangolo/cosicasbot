#!/usr/bin/env python
# -*- coding: utf-8 -*-

from decimal import Decimal
import enum
from sqlalchemy import Column, ForeignKey, ForeignKeyConstraint, Boolean, Unicode, Enum, Numeric, Text, and_
from sqlalchemy.dialects.mysql import INTEGER, BIGINT
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import exists

Base = declarative_base()


class Group(Base):
    __tablename__ = 'groups'

    id = Column(INTEGER(unsigned=True), primary_key=True)
    name = Column(Unicode(50), unique=True)

    auto_group_list = Column(Text)
    payload = Column(Text)

    users = relationship('User', secondary='roles')
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
    __tablename__ = 'users'

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

    groups = relationship('Group', secondary='roles')
    roles = relationship('Role')

    cartitems = relationship('CartItem')
    orders = relationship('Order')


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
    __tablename__ = 'roles'

    user_ref = Column(INTEGER(unsigned=True), ForeignKey('users.id'), primary_key=True)
    group_ref = Column(INTEGER(unsigned=True), ForeignKey('groups.id'), primary_key=True)
    role = Column(Enum(RoleLevel), default=RoleLevel.user)

    user = relationship('User')
    group = relationship('Group')


    @classmethod
    def exists_for_user_in_group(cls, conn, role, user_id, group_id):
        query = conn.query(exists().where(and_(Role.user_ref == user_id, Role.group_ref == group_id, Role.role == role)))
        return query.scalar()

    @classmethod
    def for_user_in_group(cls, conn, user_id, group_id):
        return conn.query(Role).filter(and_(Role.user_ref == user_id, Role.group_ref == group_id)).first()



class Catalog(Base):
    __tablename__ = 'catalogs'

    id = Column(INTEGER(unsigned=True), primary_key=True)
    name = Column(Unicode(255), nullable=False, default='')
    group_ref = Column(INTEGER(unsigned=True), ForeignKey('groups.id'), primary_key=True)

    products = relationship('Product')
    group = relationship('Group', uselist=False)


    @classmethod
    def for_user(cls, conn, user_id):
        query = conn.query(Catalog)
        query = query.join(Catalog.group)
        query = query.join(Group.roles)
        query = query.filter_by(user_ref=user_id)
        return query.all()


    @classmethod
    def by_id_for(cls, conn, catalog_id, user_id):
        query = conn.query(Catalog)
        query = query.join(Catalog.group)
        query = query.join(Group.roles)
        query = query.filter(Catalog.id == catalog_id, Role.user_ref == user_id)
        return query.one()


    def product_count(self, conn):
        return conn.query(Product).filter_by(catalog_ref=self.id).count()


    def product_page(self, conn, page, page_size):
        query = conn.query(Product).filter_by(catalog_ref=self.id)
        query = query.order_by(Product.weight, Product.name)
        query = query.offset(page * page_size).limit(page_size)
        return query.all()


class Product(Base):
    __tablename__ = 'products'

    id = Column(INTEGER(unsigned=True), primary_key=True)
    model = Column(INTEGER(unsigned=True), primary_key=True)
    catalog_ref = Column(INTEGER(unsigned=True), ForeignKey('catalogs.id'))
    weight = Column(INTEGER, nullable=False, default=10)
    active = Column(Boolean, nullable=False, default=True)
    name = Column(Unicode(255), nullable=False, default='')
    price = Column(Numeric(precision=10, scale=2), nullable=False, default=0)
    tax = Column(Numeric(precision=10, scale=2), nullable=False, default=0)
    source_ref = Column(INTEGER(unsigned=True), nullable=True)
    source_model = Column(INTEGER(unsigned=True), nullable=True)

    detail = Column(Unicode(255), nullable=False, default='')

    __table_args__ = (ForeignKeyConstraint([source_ref, source_model],
                                           [id, model]),
                      {})

    catalog = relationship('Catalog', uselist=False)
    source = relationship('Product', uselist=False)


    @classmethod
    def by_id_from_catalog_for(cls, conn, product_id, product_model, catalog_id, user_id, only_active=True):
        query = conn.query(Product)
        query = query.join(Product.catalog)
        query = query.join(Catalog.group)
        query = query.join(Group.roles)
        query = query.filter(Product.id == product_id, Product.model == product_model, Catalog.id == catalog_id, Role.user_ref == user_id)

        if only_active:
            query = query.filter(Product.active == True)

        return query.one()

    # TODO: Listener to set id and model


class OrderStatus(enum.Enum):
    received = 1
    accepted = 2
    need_info = 3
    invoiced = 4
    paid = 5
    procesing = 6
    shipped = 7


class Order(Base):
    __tablename__ = 'orders'

    id = Column(INTEGER(unsigned=True), primary_key=True)
    user_ref = Column(INTEGER(unsigned=True), ForeignKey('users.id'), nullable=False)
    catalog_ref = Column(INTEGER(unsigned=True), ForeignKey('catalogs.id'), nullable=False)
    status = Column(Enum(OrderStatus), default=OrderStatus.received)

    shipping_price = Column(Numeric(precision=10, scale=2), nullable=False, default=0)
    shipping_tax = Column(Numeric(precision=10, scale=2), nullable=False, default=0)

    customer_notes = Column(Unicode(255), nullable=False, default='')
    status_notes = Column(Unicode(255), nullable=False, default='')
    invoice_to = Column(Unicode(255), nullable=False, default='')
    ship_to = Column(Unicode(255), nullable=False, default='')

    # TODO: Cache subtotal and total

    user = relationship('User', uselist=False)
    catalog = relationship('Catalog', uselist=False)
    lineitems = relationship('LineItem')


    @classmethod
    def for_user(cls, conn, user_id):
        return conn.query(Order).filter_by(user_ref = user_id).all()


    # TODO: get values from config
    @classmethod
    def _shipping_price(cls, subtotal):
        if subtotal >= 30:
            return Decimal('0')
        elif subtotal >=15:
            return Decimal('2.48')
        else:
            return Decimal('4.96')


    def subtotal(self):
        subtotal = Decimal('0')
        taxes = Decimal('0')
        for lineitem in self.lineitems:
            subtotal += lineitem.price * lineitem.quantity
            taxes += lineitem.tax * lineitem.quantity

        return subtotal, taxes


    def total(self):
        subtotal, taxes = self.subtotal()
        return subtotal + taxes + (self.shipping_price * (1 + self.shipping_tax))


    def status_display(self, t):
        text_name = 'order_status_{}'.format(self.status.name)
        return getattr(t, text_name)


class LineItem(Base):
    __tablename__ = 'lineitems'

    order_ref = Column(INTEGER(unsigned=True), ForeignKey('orders.id'), nullable=False, primary_key=True)
    product_ref = Column(INTEGER(unsigned=True), nullable=False, primary_key=True)
    product_model = Column(INTEGER(unsigned=True), nullable=False, primary_key=True)
    price = Column(Numeric(precision=10, scale=2), nullable=False, default=0)
    tax = Column(Numeric(precision=10, scale=2), nullable=False, default=0)
    quantity = Column(INTEGER(unsigned=True), nullable=False, default=1)

    notes = Column(Unicode(255), nullable=False, default='')


    __table_args__ = (ForeignKeyConstraint([product_ref, product_model],
                                           [Product.id, Product.model]),
                      {})

    order = relationship('Order', uselist=False)
    product = relationship('Product', uselist=False)


class CartItem(Base):
    __tablename__ = 'cartitems'

    user_ref = Column(INTEGER(unsigned=True), ForeignKey('users.id'), nullable=False, primary_key=True)
    product_ref = Column(INTEGER(unsigned=True), nullable=False, primary_key=True)
    product_model = Column(INTEGER(unsigned=True), nullable=False, primary_key=True)
    quantity = Column(INTEGER(unsigned=True), nullable=False, default=1)


    __table_args__ = (ForeignKeyConstraint([product_ref, product_model],
                                           [Product.id, Product.model]),
                      {})

    user = relationship('User', uselist=False)
    product = relationship('Product', uselist=False)


class Discount(Base):
    __tablename__ = 'discounts'

    id = Column(INTEGER(unsigned=True), primary_key=True)

    product_ref = Column(INTEGER(unsigned=True), index=True)
    model_ref = Column(INTEGER(unsigned=True))
    catalog_ref = Column(INTEGER(unsigned=True), index=True)
    group_ref = Column(INTEGER(unsigned=True), index=True)
    user_ref = Column(INTEGER(unsigned=True), index=True)

    discount_price = Column(Numeric(precision=10, scale=2), default=0)
    discount_percent = Column(Numeric(precision=10, scale=2), default=0)



