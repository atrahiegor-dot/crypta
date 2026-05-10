from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


# ─── Auth ─────────────────────────────────────────────────────────────────────


class AuthRequest(BaseModel):
    init_data: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ─── Achievements ─────────────────────────────────────────────────────────────


class AchievementOut(BaseModel):
    type: str
    earned_at: datetime

    class Config:
        from_attributes = True


# ─── Profile ──────────────────────────────────────────────────────────────────


class UserProfile(BaseModel):
    id: int
    telegram_id: int
    username: Optional[str]
    first_name: str
    last_name: Optional[str]
    display_name: str
    xp_points: int
    level: int
    wallet_address: Optional[str]
    wallet_connected: bool
    daily_streak: int
    referral_code: str
    role: str
    achievements: List[AchievementOut]
    tasks_completed: int
    referrals_count: int
    rank: int

    class Config:
        from_attributes = True


# ─── Tasks ────────────────────────────────────────────────────────────────────


class TaskOut(BaseModel):
    id: int
    title: str
    description: str
    category: str
    difficulty: str
    xp_reward: int
    requires_photo: bool
    requires_video: bool
    requires_link: bool
    link_hint: Optional[str]
    is_repeatable: bool
    requires_moderation: bool
    completions_count: int
    max_completions: Optional[int]

    class Config:
        from_attributes = True


class TaskWithStatus(TaskOut):
    user_status: str  # not_started | pending | completed | rejected


class SubmissionOut(BaseModel):
    id: int
    task_id: int
    task_title: Optional[str] = None
    status: str
    submitted_at: datetime
    reviewed_at: Optional[datetime]
    xp_awarded: int
    review_comment: Optional[str]
    proof_link: Optional[str]
    proof_file_url: Optional[str]

    class Config:
        from_attributes = True


class SubmitTaskRequest(BaseModel):
    proof_link: Optional[str] = None
    proof_text: Optional[str] = None


# ─── Leaderboard ──────────────────────────────────────────────────────────────


class LeaderboardEntry(BaseModel):
    rank: int
    user_id: int
    username: Optional[str]
    first_name: str
    display_name: str
    xp_points: int
    level: int
    is_current_user: bool = False


# ─── Wallet ───────────────────────────────────────────────────────────────────


class WalletConnectRequest(BaseModel):
    wallet_address: str


class WalletStatus(BaseModel):
    connected: bool
    address: Optional[str]
    connected_at: Optional[datetime]


# ─── Moderation ───────────────────────────────────────────────────────────────


class ModerationSubmission(BaseModel):
    id: int
    user_id: int
    user_display_name: str
    task_id: int
    task_title: str
    status: str
    submitted_at: datetime
    proof_link: Optional[str]
    proof_text: Optional[str]
    proof_file_url: Optional[str]

    class Config:
        from_attributes = True


class ReviewRequest(BaseModel):
    comment: Optional[str] = None


# ─── Generic ──────────────────────────────────────────────────────────────────


class MessageResponse(BaseModel):
    message: str
    xp_awarded: Optional[int] = None
