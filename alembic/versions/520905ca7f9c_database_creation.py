"""database_creation

Revision ID: 520905ca7f9c
Revises:
Create Date: 2019-04-17 21:35:13.048718

"""
from alembic import op
import enum
import sqlalchemy as sa
import sqlalchemy.dialects.mysql as my
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import text


# revision identifiers, used by Alembic.
revision = '520905ca7f9c'
down_revision = None
branch_labels = None
depends_on = None

USER_TABLE_NAME = 'users'
GROUP_TABLE_NAME = 'groups'
ROLE_TABLE_NAME = 'roles'
CATALOG_TABLE_NAME = 'catalogs'
PRODUCT_TABLE_NAME = 'products'
LINEITEM_TABLE_NAME = 'lineitems'
ORDER_TABLE_NAME = 'orders'
CARTITEM_TABLE_NAME = 'cartitems'
DISCOUNT_TABLE_NAME = 'discounts'

GROUP_FK_NAME = 'fk_usergroups_roles'
USER_FK_NAME = 'fk_users_roles'

CATALOG_GROUP_FK_NAME = 'fk_catalogs_groups'

ORDER_USER_FK_NAME = 'fk_orders_users'

PRODUCT_CATALOG_FK_NAME = 'fk_products_catalogs'

LINEITEM_PRODUCT_FK_NAME = 'fk_lineitems_products'
LINEITEM_ORDER_FK_NAME = 'fk_lineitems_orders'

CARTITEM_PRODUCT_FK_NAME = 'fk_cartitems_products'
CARTITEM_USER_FK_NAME = 'fk_cartitems_users'


class RoleLevel(enum.Enum):
    user = 1
    moderator = 2
    admin = 3


class OrderStatus(enum.Enum):
    received = 1
    accepted = 2
    need_info = 3
    invoiced = 4
    paid = 5
    procesing = 6
    shipped = 7


def upgrade():
    conn = op.get_bind()

    op.create_table(
        GROUP_TABLE_NAME,
        sa.Column('id', my.INTEGER(unsigned=True), primary_key=True),
        sa.Column('name', sa.Unicode(50), unique=True),
        sa.Column('payload', sa.Text),
        sa.Column('auto_group_list', sa.Text)
    )


    op.create_table(
        USER_TABLE_NAME,
        sa.Column('id', my.INTEGER(unsigned=True), primary_key=True),
        sa.Column('telegram_id', my.BIGINT(unsigned=True), unique=True),
        sa.Column('telegram_handle', sa.Unicode(32)),
        sa.Column('name', sa.Unicode(20)),
        sa.Column('lastname', sa.Unicode(50)),
        sa.Column('vat_id', sa.Unicode(20), unique=True),
        sa.Column('invoice_address', sa.Unicode(250)),
        sa.Column('shipping_address', sa.Unicode(250)),
        sa.Column('email_address', sa.Unicode(50)),
        sa.Column('phone_number', sa.Unicode(20))
    )

    op.create_table(
        ROLE_TABLE_NAME,
        sa.Column('user_ref', my.INTEGER(unsigned=True), primary_key=True),
        sa.Column('group_ref', my.INTEGER(unsigned=True), primary_key=True),
        sa.Column('role', sa.Enum(RoleLevel), default=RoleLevel.user)
    )

    op.create_foreign_key(
        GROUP_FK_NAME,
        ROLE_TABLE_NAME, GROUP_TABLE_NAME,
        ['group_ref'], ['id'],
    )

    op.create_foreign_key(
        USER_FK_NAME,
        ROLE_TABLE_NAME, USER_TABLE_NAME,
        ['user_ref'], ['id'],
    )


    op.create_table(
        CATALOG_TABLE_NAME,
        sa.Column('id', my.INTEGER(unsigned=True), primary_key=True),
        sa.Column('name', sa.Unicode(255), nullable=False, default=''),
        sa.Column('group_ref', my.INTEGER(unsigned=True), nullable=False)
    )

    op.create_foreign_key(
        CATALOG_GROUP_FK_NAME,
        CATALOG_TABLE_NAME, GROUP_TABLE_NAME,
        ['group_ref'], ['id']
    )


    op.create_table(
        ORDER_TABLE_NAME,
        sa.Column('id', my.INTEGER(unsigned=True), primary_key=True),
        sa.Column('user_ref', my.INTEGER(unsigned=True), nullable=False),

        sa.Column('catalog_ref', my.INTEGER(unsigned=True), nullable=False),

        sa.Column('status', sa.Enum(OrderStatus), default=OrderStatus.received),
        sa.Column('shipping_price', sa.Numeric(precision=10, scale=2), nullable=False, default=0),
        sa.Column('shipping_tax', sa.Numeric(precision=10, scale=2), nullable=False, default=0),

        sa.Column('customer_notes', sa.Unicode(255), nullable=False, default=''),
        sa.Column('status_notes', sa.Unicode(255), nullable=False, default=''),
        sa.Column('invoice_to', sa.Unicode(255), nullable=False, default=''),
        sa.Column('ship_to', sa.Unicode(255), nullable=False, default='')
    )

    op.create_foreign_key(
        ORDER_USER_FK_NAME,
        ORDER_TABLE_NAME, USER_TABLE_NAME,
        ['user_ref'], ['id']
    )


    op.create_table(
        PRODUCT_TABLE_NAME,
        sa.Column('id', my.INTEGER(unsigned=True), primary_key=True),
        sa.Column('model', my.INTEGER(unsigned=True), primary_key=True),
        sa.Column('catalog_ref', my.INTEGER(unsigned=True), nullable=False),
        sa.Column('active', sa.Boolean, nullable=False, default=True),
        sa.Column('name', sa.Unicode(255), nullable=False, default=''),
        sa.Column('price', sa.Numeric(precision=10, scale=2), nullable=False, default=0),
        sa.Column('tax', sa.Numeric(precision=10, scale=2), nullable=False, default=0),

        sa.Column('detail', sa.Unicode(255), nullable=False, default=''),
    )

    op.create_foreign_key(
        PRODUCT_CATALOG_FK_NAME,
        PRODUCT_TABLE_NAME, CATALOG_TABLE_NAME,
        ['catalog_ref'], ['id']
    )


    op.create_table(
        LINEITEM_TABLE_NAME,
        sa.Column('order_ref', my.INTEGER(unsigned=True), primary_key=True),
        sa.Column('product_ref', my.INTEGER(unsigned=True), primary_key=True),
        sa.Column('product_model', my.INTEGER(unsigned=True), primary_key=True),
        sa.Column('price', sa.Numeric(precision=10, scale=2), nullable=False, default=0),
        sa.Column('tax', sa.Numeric(precision=10, scale=2), nullable=False, default=0),
        sa.Column('quantity', my.INTEGER(unsigned=True), nullable=False, default=1),
        sa.Column('notes', sa.Unicode(255), nullable=False, default='')
    )

    op.create_foreign_key(
        LINEITEM_ORDER_FK_NAME,
        LINEITEM_TABLE_NAME, ORDER_TABLE_NAME,
        ['order_ref'], ['id']
    )

    op.create_foreign_key(
        LINEITEM_PRODUCT_FK_NAME,
        LINEITEM_TABLE_NAME, PRODUCT_TABLE_NAME,
        ['product_ref', 'product_model'], ['id', 'model']
    )


    op.create_table(
        CARTITEM_TABLE_NAME,
        sa.Column('user_ref', my.INTEGER(unsigned=True), primary_key=True),
        sa.Column('product_ref', my.INTEGER(unsigned=True), primary_key=True),
        sa.Column('product_model', my.INTEGER(unsigned=True), primary_key=True),
        sa.Column('quantity', my.INTEGER(unsigned=True), nullable=False, default=1)
    )

    op.create_foreign_key(
        CARTITEM_USER_FK_NAME,
        CARTITEM_TABLE_NAME, USER_TABLE_NAME,
        ['user_ref'], ['id']
    )

    op.create_foreign_key(
        CARTITEM_PRODUCT_FK_NAME,
        CARTITEM_TABLE_NAME, PRODUCT_TABLE_NAME,
        ['product_ref', 'product_model'], ['id', 'model']
    )


    op.create_table(
        DISCOUNT_TABLE_NAME,
        sa.Column('id', my.INTEGER(unsigned=True), primary_key=True),
        sa.Column('product_ref', my.INTEGER(unsigned=True), index=True),
        sa.Column('product_model', my.INTEGER(unsigned=True)),
        sa.Column('catalog_ref', my.INTEGER(unsigned=True), index=True),
        sa.Column('group_ref', my.INTEGER(unsigned=True), index=True),
        sa.Column('user_ref', my.INTEGER(unsigned=True), index=True),
        sa.Column('discount_price', sa.Numeric(precision=10, scale=2), default=0),
        sa.Column('discount_percent', sa.Numeric(precision=10, scale=2), default=0)
    )

   # --- INSERT GROUPS

    conn.execute('INSERT INTO `groups` (id, name, auto_group_list) VALUES (1, "Admin", NULL)')
    conn.execute('INSERT INTO `groups` (id, name, auto_group_list) VALUES (2, "All Users", "all")')

   # Save first 100 groups for special bot groups.
    conn.execute('ALTER TABLE `groups` AUTO_INCREMENT=100')


def downgrade():
    op.drop_table(DISCOUNT_TABLE_NAME)

    op.drop_constraint(CARTITEM_PRODUCT_FK_NAME, CARTITEM_TABLE_NAME, type_='foreignkey')
    op.drop_constraint(CARTITEM_USER_FK_NAME, CARTITEM_TABLE_NAME, type_='foreignkey')
    op.drop_table(CARTITEM_TABLE_NAME)

    op.drop_constraint(LINEITEM_PRODUCT_FK_NAME, LINEITEM_TABLE_NAME, type_='foreignkey')
    op.drop_constraint(LINEITEM_ORDER_FK_NAME, LINEITEM_TABLE_NAME, type_='foreignkey')
    op.drop_table(LINEITEM_TABLE_NAME)

    op.drop_constraint(PRODUCT_CATALOG_FK_NAME, PRODUCT_TABLE_NAME, type_='foreignkey')
    op.drop_table(PRODUCT_TABLE_NAME)

    op.drop_constraint(ORDER_USER_FK_NAME, ORDER_TABLE_NAME, type_='foreignkey')
    op.drop_table(ORDER_TABLE_NAME)

    op.drop_constraint(CATALOG_GROUP_FK_NAME, CATALOG_TABLE_NAME, type_='foreignkey')
    op.drop_table(CATALOG_TABLE_NAME)

    op.drop_constraint(GROUP_FK_NAME, USER_TABLE_NAME, type_='foreignkey')
    op.drop_constraint(USER_FK_NAME, GROUP_TABLE_NAME, type_='foreignkey')
    op.drop_table(ROLE_TABLE_NAME)

    op.drop_table(USER_TABLE_NAME)

    op.drop_table(ORG_TABLE_NAME)

