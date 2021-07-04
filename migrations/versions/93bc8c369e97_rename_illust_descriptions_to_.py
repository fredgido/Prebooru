"""Rename illust descriptions to commentaries

Revision ID: 93bc8c369e97
Revises: 70ba243ba217
Create Date: 2021-07-03 15:42:47.177717

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '93bc8c369e97'
down_revision = '70ba243ba217'
branch_labels = None
depends_on = None


NAMING_CONVENTION = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


def upgrade_():
    #op.rename_table('illust_commentaries', 'illust_descriptions')
    #return
    op.rename_table('illust_descriptions', 'illust_commentaries')
    with op.batch_alter_table('illust_commentaries', schema=None, naming_convention=NAMING_CONVENTION) as batch_op:
        batch_op.drop_constraint('pk_illust_descriptions', type_='primary')
        batch_op.drop_constraint('fk_illust_descriptions_description_id_description', type_='foreignkey')
        batch_op.drop_constraint('fk_illust_descriptions_illust_id_illust', type_='foreignkey')
        batch_op.create_primary_key('pk_illust_commentaries', ['description_id', 'illust_id'])
        batch_op.create_foreign_key('fk_illust_commentaries_description_id_description', 'description', ['description_id'], ['id'])
        batch_op.create_foreign_key('fk_illust_commentaries_illust_id_illust', 'illust', ['illust_id'], ['id'])


def downgrade_():
    op.rename_table('illust_commentaries', 'illust_descriptions')
    with op.batch_alter_table('illust_descriptions', schema=None, naming_convention=NAMING_CONVENTION) as batch_op:
        batch_op.drop_constraint('pk_illust_commentaries', type_='primary')
        batch_op.drop_constraint('fk_illust_commentaries_description_id_description', type_='foreignkey')
        batch_op.drop_constraint('fk_illust_commentaries_illust_id_illust', type_='foreignkey')
        batch_op.create_primary_key('pk_illust_descriptions', ['description_id', 'illust_id'])
        batch_op.create_foreign_key('fk_illust_descriptions_description_id_description', 'description', ['description_id'], ['id'])
        batch_op.create_foreign_key('fk_illust_descriptions_illust_id_illust', 'illust', ['illust_id'], ['id'])


def upgrade_cache():
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###


def downgrade_cache():
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###


def upgrade_similarity():
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###


def downgrade_similarity():
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###
