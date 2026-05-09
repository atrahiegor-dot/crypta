import enum
import random
import string
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger, Boolean, Column, DateTime, Enum, ForeignKey,
    Integer, Numeric, String, Text, JSON, UniqueConstraint,
)
from sqlalchemy.orm import relationship

from bot.database.base import Base


# ─── Enums ────────────────────────────────────────────────────────────────────

class UserRole(str, enum.Enum):
    USER = "user"
    MODERATOR = "moderator"
    DEVELOPER = "developer"


class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class TaskCategory(str, enum.Enum):
    SOCIAL = "social"
    COMMUNITY = "community"
    DEVELOPMENT = "development"
    CREATIVE = "creative"
    SPECIAL = "special"


class TaskDifficulty(str, enum.Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    LEGENDARY = "legendary"


class AchievementType(str, enum.Enum):
    FIRST_TASK = "first_task"
    TASKS_10 = "tasks_10"
    TASKS_50 = "tasks_50"
    TASKS_100 = "tasks_100"
    LEVEL_5 = "level_5"
    LEVEL_10 = "level_10"
    LEVEL_25 = "level_25"
    WALLET_CONNECTED = "wallet_connected"
    FIRST_REFERRAL = "first_referral"
    REFERRALS_10 = "referrals_10"
    TOP_10_LEADERBOARD = "top_10_leaderboard"
    DAILY_STREAK_7 = "daily_streak_7"
    DAILY_STREAK_30 = "daily_streak_30"


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _gen_referral_code() -> str:
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=8))


# ─── Models ───────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=False)
    last_name = Column(String(255), nullable=True)
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)

    # Balances
    xp_points = Column(BigInteger, default=0, nullable=False)
    internal_balance_tt = Column(Numeric(20, 8), default=Decimal("0"), nullable=False)
    level = Column(Integer, default=1, nullable=False)

    # Wallet
    wallet_address = Column(String(255), nullable=True, unique=True)
    wallet_connected_at = Column(DateTime(timezone=True), nullable=True)

    # Referral
    referral_code = Column(String(20), unique=True, nullable=False, default=_gen_referral_code)
    referred_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Status
    is_banned = Column(Boolean, default=False, nullable=False)
    ban_reason = Column(String(500), nullable=True)

    # Streak
    daily_streak = Column(Integer, default=0, nullable=False)
    last_checkin_date = Column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    last_activity = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    # Relationships
    task_submissions = relationship(
        "TaskSubmission", foreign_keys="TaskSubmission.user_id", back_populates="user",
        lazy="selectin",
    )
    reviewed_submissions = relationship(
        "TaskSubmission", foreign_keys="TaskSubmission.reviewer_id", back_populates="reviewer",
    )
    referrals_made = relationship(
        "Referral", foreign_keys="Referral.referrer_id", back_populates="referrer",
    )
    achievements = relationship("Achievement", back_populates="user", lazy="selectin")
    daily_checkins = relationship("DailyCheckIn", back_populates="user")

    @property
    def display_name(self) -> str:
        if self.username:
            return f"@{self.username}"
        parts = [self.first_name]
        if self.last_name:
            parts.append(self.last_name)
        return " ".join(parts)


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(Enum(TaskCategory), nullable=False)
    difficulty = Column(Enum(TaskDifficulty), default=TaskDifficulty.EASY, nullable=False)

    xp_reward = Column(Integer, nullable=False, default=100)
    tt_reward = Column(Numeric(20, 8), default=Decimal("0"), nullable=False)

    requires_moderation = Column(Boolean, default=True, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_repeatable = Column(Boolean, default=False, nullable=False)

    # Proof requirements
    requires_photo = Column(Boolean, default=False, nullable=False)
    requires_video = Column(Boolean, default=False, nullable=False)
    requires_link = Column(Boolean, default=False, nullable=False)
    link_hint = Column(String(500), nullable=True)

    # Limits
    max_completions = Column(Integer, nullable=True)
    completions_count = Column(Integer, default=0, nullable=False)

    # Availability window
    available_from = Column(DateTime(timezone=True), nullable=True)
    available_until = Column(DateTime(timezone=True), nullable=True)

    created_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    submissions = relationship("TaskSubmission", back_populates="task")
    created_by = relationship("User", foreign_keys=[created_by_id])


class TaskSubmission(Base):
    __tablename__ = "task_submissions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)

    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING, nullable=False)

    # Proof materials
    proof_text = Column(Text, nullable=True)
    proof_photo_file_id = Column(String(500), nullable=True)
    proof_video_file_id = Column(String(500), nullable=True)
    proof_link = Column(String(1000), nullable=True)

    # Review info
    reviewer_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    review_comment = Column(Text, nullable=True)
    xp_awarded = Column(Integer, default=0, nullable=False)

    submitted_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="task_submissions")
    task = relationship("Task", back_populates="submissions")
    reviewer = relationship("User", foreign_keys=[reviewer_id], back_populates="reviewed_submissions")


class Referral(Base):
    __tablename__ = "referrals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    referrer_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    referred_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)

    xp_earned_referrer = Column(Integer, default=0, nullable=False)
    xp_earned_referred = Column(Integer, default=0, nullable=False)

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    # Relationships
    referrer = relationship("User", foreign_keys=[referrer_id], back_populates="referrals_made")
    referred = relationship("User", foreign_keys=[referred_id])


class Achievement(Base):
    __tablename__ = "achievements"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    achievement_type = Column(Enum(AchievementType), nullable=False)
    earned_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    meta = Column(JSON, nullable=True)

    __table_args__ = (
        UniqueConstraint("user_id", "achievement_type", name="uq_user_achievement"),
    )

    user = relationship("User", back_populates="achievements")


class DailyCheckIn(Base):
    __tablename__ = "daily_checkins"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    checked_in_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    streak = Column(Integer, default=1, nullable=False)
    xp_earned = Column(Integer, default=0, nullable=False)

    user = relationship("User", back_populates="daily_checkins")


class BonusEvent(Base):
    __tablename__ = "bonus_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    xp_multiplier = Column(Numeric(5, 2), default=Decimal("1.0"), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    starts_at = Column(DateTime(timezone=True), nullable=False)
    ends_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
