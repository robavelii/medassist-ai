"""Add cost and token tracking to LLMCache (manual)

Revision ID: e86e8e81d4b6
Revises: e5b4f6f9ca59
Create Date: 2025-08-25 12:59:33.946516

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e86e8e81d4b6"
down_revision: Union[str, Sequence[str], None] = "e5b4f6f9ca59"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("llm_cache", sa.Column("model_name", sa.String(length=50), nullable=True))
    op.add_column("llm_cache", sa.Column("input_tokens", sa.Integer(), nullable=True))
    op.add_column("llm_cache", sa.Column("output_tokens", sa.Integer(), nullable=True))
    op.add_column("llm_cache", sa.Column("total_cost", sa.Float(), nullable=True))

    # Populate existing rows with default values
    op.execute("UPDATE llm_cache SET model_name = 'gpt-4o' WHERE model_name IS NULL")
    op.execute("UPDATE llm_cache SET input_tokens = 0 WHERE input_tokens IS NULL")
    op.execute("UPDATE llm_cache SET output_tokens = 0 WHERE output_tokens IS NULL")
    op.execute("UPDATE llm_cache SET total_cost = 0.0 WHERE total_cost IS NULL")

    # Alter columns to be non-nullable
    op.alter_column("llm_cache", "model_name", existing_type=sa.String(length=50), nullable=False)
    op.alter_column("llm_cache", "input_tokens", existing_type=sa.Integer(), nullable=False)
    op.alter_column("llm_cache", "output_tokens", existing_type=sa.Integer(), nullable=False)
    op.alter_column("llm_cache", "total_cost", existing_type=sa.Float(), nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("llm_cache", "total_cost")
    op.drop_column("llm_cache", "output_tokens")
    op.drop_column("llm_cache", "input_tokens")
    op.drop_column("llm_cache", "model_name")
