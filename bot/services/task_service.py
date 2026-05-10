"""Task business logic service."""
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from bot.database import crud
from bot.database.models import (
    Task, TaskSubmission, TaskStatus, AchievementType, User,
)
from bot.services.xp_service import xp_service


class TaskService:
    async def can_submit_task(
        self, session: AsyncSession, user: User, task: Task
    ) -> tuple[bool, str]:
        """Check if the user is eligible to submit this task."""
        if not task.is_active:
            return False, "Задание неактивно."

        now = datetime.now(timezone.utc)
        if task.available_from and now < task.available_from:
            return False, "Задание ещё не доступно."
        if task.available_until and now > task.available_until:
            return False, "Задание уже завершено."

        if task.max_completions and task.completions_count >= task.max_completions:
            return False, "Лимит выполнений задания исчерпан."

        if not task.is_repeatable:
            completed = await crud.has_user_completed_task(session, user.id, task.id)
            if completed:
                return False, "Вы уже выполнили это задание."

        pending = await crud.has_user_pending_submission(session, user.id, task.id)
        if pending:
            return False, "У вас уже есть заявка на проверке для этого задания."

        return True, ""

    async def submit_task(
        self,
        session: AsyncSession,
        user: User,
        task: Task,
        proof_text: Optional[str] = None,
        proof_photo_file_id: Optional[str] = None,
        proof_video_file_id: Optional[str] = None,
        proof_link: Optional[str] = None,
    ) -> TaskSubmission:
        sub = await crud.create_submission(
            session,
            user_id=user.id,
            task_id=task.id,
            proof_text=proof_text,
            proof_photo_file_id=proof_photo_file_id,
            proof_video_file_id=proof_video_file_id,
            proof_link=proof_link,
        )

        # Auto-approve tasks that don't need moderation
        if not task.requires_moderation:
            await self._approve_submission(session, sub, task, user)

        return sub

    async def _approve_submission(
        self,
        session: AsyncSession,
        sub: TaskSubmission,
        task: Task,
        user: User,
    ) -> None:
        bonus_event = await crud.get_active_bonus_event(session)
        multiplier = float(bonus_event.xp_multiplier) if bonus_event else 1.0

        actual_xp, leveled_up, new_achievements = await xp_service.award_xp(
            session, user, task.xp_reward, multiplier
        )
        sub.status = TaskStatus.APPROVED
        sub.xp_awarded = actual_xp
        sub.reviewed_at = datetime.now(timezone.utc)
        task.completions_count += 1

        # Task completion achievements
        total_done = len([s for s in user.task_submissions if s.status == TaskStatus.APPROVED])
        if total_done >= 1:
            await crud.grant_achievement(session, user.id, AchievementType.FIRST_TASK)
        if total_done >= 10:
            await crud.grant_achievement(session, user.id, AchievementType.TASKS_10)
        if total_done >= 50:
            await crud.grant_achievement(session, user.id, AchievementType.TASKS_50)
        if total_done >= 100:
            await crud.grant_achievement(session, user.id, AchievementType.TASKS_100)

    async def approve_submission(
        self,
        session: AsyncSession,
        submission_id: int,
        reviewer_id: int,
        comment: Optional[str] = None,
    ) -> Optional[TaskSubmission]:
        sub = await crud.get_submission_by_id(session, submission_id)
        if not sub or sub.status != TaskStatus.PENDING:
            return None

        task = await crud.get_task_by_id(session, sub.task_id)
        user = await crud.get_user_by_id(session, sub.user_id)

        bonus_event = await crud.get_active_bonus_event(session)
        multiplier = float(bonus_event.xp_multiplier) if bonus_event else 1.0

        actual_xp, _, _ = await xp_service.award_xp(
            session, user, task.xp_reward, multiplier
        )

        await crud.review_submission(
            session,
            submission_id=submission_id,
            reviewer_id=reviewer_id,
            status=TaskStatus.APPROVED,
            comment=comment,
            xp_awarded=actual_xp,
        )
        task.completions_count += 1
        return sub

    async def reject_submission(
        self,
        session: AsyncSession,
        submission_id: int,
        reviewer_id: int,
        comment: Optional[str] = None,
    ) -> Optional[TaskSubmission]:
        sub = await crud.get_submission_by_id(session, submission_id)
        if not sub or sub.status != TaskStatus.PENDING:
            return None

        await crud.review_submission(
            session,
            submission_id=submission_id,
            reviewer_id=reviewer_id,
            status=TaskStatus.REJECTED,
            comment=comment,
            xp_awarded=0,
        )
        return sub


task_service = TaskService()
