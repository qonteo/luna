"""add indexes

Revision ID: 17d57fc3a9fb
Revises: 464ee60b8440
Create Date: 2018-11-13 11:56:37.996622

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '17d57fc3a9fb'
down_revision = '2845eb6e9edb'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_index('index_list_id_link_key', 'list_face', ['list_id', sa.text("link_key DESC")], unique=True)
    op.create_index('index_list_id_unlink_key', 'unlink_attributes_log', ['list_id', sa.text("unlink_key DESC")],
                    unique=True)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index('index_list_id_link_key', table_name='list_face')
    op.drop_index('index_list_id_unlink_key', table_name='unlink_attributes_log')
    # ### end Alembic commands ###
