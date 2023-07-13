"""create tanks, tankvolumes, and averagesales tables

Revision ID: cd51f9f25127
Revises:
Create Date: 2023-07-13 12:38:42.664692

"""
import sqlalchemy as sa
import sqlmodel

from alembic import op

# revision identifiers, used by Alembic.
revision = 'cd51f9f25127'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('tank',
    sa.Column('name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('averagesale',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('tank_id', sa.Integer(), nullable=False),
    sa.Column('date', sa.Date(), nullable=False),
    sa.Column('sales', sa.Integer(), nullable=False),
    sa.Column('total', sa.Float(), nullable=False),
    sa.ForeignKeyConstraint(['tank_id'], ['tank.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('tankvolume',
    sa.Column('volume', sa.Float(), nullable=False),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('tank_id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['tank_id'], ['tank.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tankvolume_created_at'), 'tankvolume', ['created_at'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_tankvolume_created_at'), table_name='tankvolume')
    op.drop_table('tankvolume')
    op.drop_table('averagesale')
    op.drop_table('tank')
    # ### end Alembic commands ###