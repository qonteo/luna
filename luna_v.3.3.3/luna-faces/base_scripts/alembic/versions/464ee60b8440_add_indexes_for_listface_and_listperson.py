"""add indexes for listFace and listPerson

Revision ID: 464ee60b8440
Revises: bed22c866b16
Create Date: 2018-09-19 11:07:56.158500

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '464ee60b8440'
down_revision = 'bed22c866b16'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index('ix_face_create_time', table_name='face')
    op.create_index(op.f('ix_list_face_face_id'), 'list_face', ['face_id'], unique=False)
    op.create_index(op.f('ix_list_person_person_id'), 'list_person', ['person_id'], unique=False)
    op.drop_index('ix_person_create_time', table_name='person')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_index('ix_person_create_time', 'person', ['create_time'], unique=False)
    op.drop_index(op.f('ix_list_person_person_id'), table_name='list_person')
    op.drop_index(op.f('ix_list_face_face_id'), table_name='list_face')
    op.create_index('ix_face_create_time', 'face', ['create_time'], unique=False)
    # ### end Alembic commands ###