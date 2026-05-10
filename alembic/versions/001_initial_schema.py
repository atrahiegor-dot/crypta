"""Initial schema

Revision ID: 001
Revises:
Create Date: 2025-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("username", sa.String(255), nullable=True),
        sa.Column("first_name", sa.String(255), nullable=False),
        sa.Column("last_name", sa.String(255), nullable=True),
        sa.Column("role", sa.Enum("user", "moderator", "developer", name="userrole"), nullable=False, server_default="user"),
        sa.Column("xp_points", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("internal_balance_tt", sa.Numeric(20, 8), nullable=False, server_default="0"),
        sa.Column("level", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("wallet_address", sa.String(255), nullable=True),
        sa.Column("wallet_connected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("referral_code", sa.String(20), nullable=False),
        sa.Column("referred_by_id", sa.Integer(), nullable=True),
        sa.Column("is_banned", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("ban_reason", sa.String(500), nullable=True),
        sa.Column("daily_streak", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_checkin_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_activity", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(["referred_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("telegram_id"),
        sa.UniqueConstraint("wallet_address"),
        sa.UniqueConstraint("referral_code"),
    )
    op.create_index("ix_users_telegram_id", "users", ["telegram_id"])

    op.create_table(
        "tasks",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("category", sa.Enum("social", "community", "development", "creative", "special", name="taskcategory"), nullable=False),
        sa.Column("difficulty", sa.Enum("easy", "medium", "hard", "legendary", name="taskdifficulty"), nullable=False, server_default="easy"),
        sa.Column("xp_reward", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("tt_reward", sa.Numeric(20, 8), nullable=False, server_default="0"),
        sa.Column("requires_moderation", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_repeatable", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("requires_photo", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("requires_video", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("requires_link", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("link_hint", sa.String(500), nullable=True),
        sa.Column("max_completions", sa.Integer(), nullable=True),
        sa.Column("completions_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("available_from", sa.DateTime(timezone=True), nullable=True),
        sa.Column("available_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "task_submissions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("task_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.Enum("pending", "approved", "rejected", "cancelled", name="taskstatus"), nullable=False, server_default="pending"),
        sa.Column("proof_text", sa.Text(), nullable=True),
        sa.Column("proof_photo_file_id", sa.String(500), nullable=True),
        sa.Column("proof_video_file_id", sa.String(500), nullable=True),
        sa.Column("proof_link", sa.String(1000), nullable=True),
        sa.Column("reviewer_id", sa.Integer(), nullable=True),
        sa.Column("review_comment", sa.Text(), nullable=True),
        sa.Column("xp_awarded", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reviewer_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_task_submissions_user_id", "task_submissions", ["user_id"])
    op.create_index("ix_task_submissions_task_id", "task_submissions", ["task_id"])

    op.create_table(
        "referrals",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("referrer_id", sa.Integer(), nullable=False),
        sa.Column("referred_id", sa.Integer(), nullable=False),
        sa.Column("xp_earned_referrer", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("xp_earned_referred", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(["referrer_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["referred_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("referred_id"),
    )
    op.create_index("ix_referrals_referrer_id", "referrals", ["referrer_id"])

    op.create_table(
        "achievements",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("achievement_type", sa.Enum(
            "first_task", "tasks_10", "tasks_50", "tasks_100",
            "level_5", "level_10", "level_25",
            "wallet_connected", "first_referral", "referrals_10",
            "top_10_leaderboard", "daily_streak_7", "daily_streak_30",
            name="achievementtype",
        ), nullable=False),
        sa.Column("earned_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("meta", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "achievement_type", name="uq_user_achievement"),
    )
    op.create_index("ix_achievements_user_id", "achievements", ["user_id"])

    op.create_table(
        "daily_checkins",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("checked_in_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("streak", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("xp_earned", sa.Integer(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_daily_checkins_user_id", "daily_checkins", ["user_id"])

    op.create_table(
        "bonus_events",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("xp_multiplier", sa.Numeric(5, 2), nullable=False, server_default="1.0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("bonus_events")
    op.drop_table("daily_checkins")
    op.drop_table("achievements")
    op.drop_table("referrals")
    op.drop_table("task_submissions")
    op.drop_table("tasks")
    op.drop_table("users")
    op.execute("DROP TYPE IF EXISTS userrole")
    op.execute("DROP TYPE IF EXISTS taskcategory")
    op.execute("DROP TYPE IF EXISTS taskdifficulty")
    op.execute("DROP TYPE IF EXISTS taskstatus")
    op.execute("DROP TYPE IF EXISTS achievementtype")
