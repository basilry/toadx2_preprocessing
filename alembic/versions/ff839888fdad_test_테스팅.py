"""[test] 테스팅

Revision ID: ff839888fdad
Revises: 0c79774765ce
Create Date: 2024-09-28 15:29:56.077597

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ff839888fdad'
down_revision: Union[str, None] = '0c79774765ce'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
