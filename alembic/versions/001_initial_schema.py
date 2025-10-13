"""Initial schema: rules, events, rule_triggers

Revision ID: 001_initial
Revises:
Create Date: 2025-01-13

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create rules table
    op.create_table(
        'rules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('uuid', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('details', sa.Text(), nullable=False),
        sa.Column('language', sa.String(length=100), nullable=False),
        sa.Column('pattern', sa.Text(), nullable=False),
        sa.Column('action', sa.String(length=50), nullable=False),
        sa.Column('severity', sa.String(length=50), nullable=True),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('cwe_id', sa.String(length=50), nullable=True),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('uuid')
    )
    op.create_index(op.f('ix_rules_uuid'), 'rules', ['uuid'], unique=True)

    # Create events table
    op.create_table(
        'events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('task_id', sa.String(length=255), nullable=True),
        sa.Column('prompt', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('flow_name', sa.String(length=100), nullable=False),
        sa.Column('pipeline_results', sa.JSON() if op.get_bind().dialect.name == 'postgresql' else sa.Text(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_events_flow_name'), 'events', ['flow_name'], unique=False)
    op.create_index(op.f('ix_events_status'), 'events', ['status'], unique=False)
    op.create_index(op.f('ix_events_task_id'), 'events', ['task_id'], unique=False)
    op.create_index(op.f('ix_events_timestamp'), 'events', ['timestamp'], unique=False)

    # Create rule_triggers table
    op.create_table(
        'rule_triggers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=False),
        sa.Column('rule_id', sa.Integer(), nullable=False),
        sa.Column('matched_text', sa.Text(), nullable=True),
        sa.Column('pipeline_name', sa.String(length=100), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['event_id'], ['events.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['rule_id'], ['rules.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_rule_triggers_event_id'), 'rule_triggers', ['event_id'], unique=False)
    op.create_index(op.f('ix_rule_triggers_rule_id'), 'rule_triggers', ['rule_id'], unique=False)
    op.create_index(op.f('ix_rule_triggers_timestamp'), 'rule_triggers', ['timestamp'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_rule_triggers_timestamp'), table_name='rule_triggers')
    op.drop_index(op.f('ix_rule_triggers_rule_id'), table_name='rule_triggers')
    op.drop_index(op.f('ix_rule_triggers_event_id'), table_name='rule_triggers')
    op.drop_table('rule_triggers')

    op.drop_index(op.f('ix_events_timestamp'), table_name='events')
    op.drop_index(op.f('ix_events_task_id'), table_name='events')
    op.drop_index(op.f('ix_events_status'), table_name='events')
    op.drop_index(op.f('ix_events_flow_name'), table_name='events')
    op.drop_table('events')

    op.drop_index(op.f('ix_rules_uuid'), table_name='rules')
    op.drop_table('rules')
