"""
Gamification Service - XP, Levels, Achievements, and Streaks
"""
import math
from datetime import date, datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.models import (
    User, Achievement, UserAchievement, Streak, DailyGoal,
    ActivityLog, Reward, UserProgress, VocabularyProgress
)
from app.config import settings


class XPService:
    """Service for managing experience points and levels"""
    
    # XP required for each level (exponential curve)
    BASE_XP = 100
    GROWTH_FACTOR = 1.5
    
    @classmethod
    def calculate_level(cls, total_xp: int) -> int:
        """Calculate level from total XP"""
        if total_xp < cls.BASE_XP:
            return 1
        
        # Level = log(total_xp / BASE_XP) / log(GROWTH_FACTOR) + 1
        level = math.log(total_xp / cls.BASE_XP) / math.log(cls.GROWTH_FACTOR) + 1
        return max(1, int(level))
    
    @classmethod
    def xp_for_level(cls, level: int) -> int:
        """Calculate XP required for a specific level"""
        if level <= 1:
            return 0
        return int(cls.BASE_XP * (cls.GROWTH_FACTOR ** (level - 1)))
    
    @classmethod
    def xp_to_next_level(cls, current_xp: int) -> int:
        """Calculate XP needed to reach next level"""
        current_level = cls.calculate_level(current_xp)
        next_level_xp = cls.xp_for_level(current_level + 1)
        return next_level_xp - current_xp
    
    @classmethod
    def get_level_progress(cls, current_xp: int) -> Dict[str, Any]:
        """Get detailed level progress information"""
        current_level = cls.calculate_level(current_xp)
        current_level_xp = cls.xp_for_level(current_level)
        next_level_xp = cls.xp_for_level(current_level + 1)
        
        xp_in_level = current_xp - current_level_xp
        xp_needed = next_level_xp - current_level_xp
        progress_percent = (xp_in_level / xp_needed) * 100 if xp_needed > 0 else 100
        
        return {
            "level": current_level,
            "current_xp": current_xp,
            "xp_in_current_level": xp_in_level,
            "xp_to_next_level": next_level_xp - current_xp,
            "progress_percent": progress_percent
        }


class StreakService:
    """Service for managing learning streaks"""
    
    @staticmethod
    async def update_streak(db: AsyncSession, user_id: str) -> Streak:
        """Update user's learning streak"""
        result = await db.execute(
            select(Streak).where(Streak.user_id == user_id)
        )
        streak = result.scalar_one_or_none()
        
        today = date.today()
        
        if streak is None:
            # Create new streak
            streak = Streak(
                user_id=user_id,
                current_streak=1,
                longest_streak=1,
                last_activity_date=today
            )
            db.add(streak)
        else:
            last_activity = streak.last_activity_date
            
            if last_activity == today:
                # Already updated today
                pass
            elif last_activity == today - timedelta(days=1):
                # Consecutive day
                streak.current_streak += 1
                streak.longest_streak = max(streak.longest_streak, streak.current_streak)
                streak.last_activity_date = today
            else:
                # Streak broken
                streak.current_streak = 1
                streak.last_activity_date = today
            
            streak.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(streak)
        return streak
    
    @staticmethod
    async def get_streak_bonus(db: AsyncSession, user_id: str) -> float:
        """Get XP bonus multiplier based on streak"""
        result = await db.execute(
            select(Streak).where(Streak.user_id == user_id)
        )
        streak = result.scalar_one_or_none()
        
        if streak is None:
            return 1.0
        
        # Bonus increases with streak, capped at 2x
        bonus = min(2.0, 1.0 + (streak.current_streak * 0.05))
        return bonus


class AchievementService:
    """Service for managing achievements"""
    
    # Achievement definitions
    ACHIEVEMENTS = [
        # Learning achievements
        {
            "name": "First Steps",
            "name_ru": "Первые шаги",
            "description": "Complete your first lesson",
            "description_ru": "Завершите свой первый урок",
            "category": "learning",
            "requirement_type": "lessons_completed",
            "requirement_value": 1,
            "xp_bonus": 50,
            "icon": "🎯"
        },
        {
            "name": "Knowledge Seeker",
            "name_ru": "Искатель знаний",
            "description": "Complete 10 lessons",
            "description_ru": "Завершите 10 уроков",
            "category": "learning",
            "requirement_type": "lessons_completed",
            "requirement_value": 10,
            "xp_bonus": 200,
            "icon": "📚"
        },
        {
            "name": "Scholar",
            "name_ru": "Учёный",
            "description": "Complete 50 lessons",
            "description_ru": "Завершите 50 уроков",
            "category": "learning",
            "requirement_type": "lessons_completed",
            "requirement_value": 50,
            "xp_bonus": 500,
            "icon": "🎓"
        },
        # Vocabulary achievements
        {
            "name": "Word Collector",
            "name_ru": "Собиратель слов",
            "description": "Learn 50 new words",
            "description_ru": "Выучите 50 новых слов",
            "category": "vocabulary",
            "requirement_type": "words_learned",
            "requirement_value": 50,
            "xp_bonus": 150,
            "icon": "📝"
        },
        {
            "name": "Vocabulary Master",
            "name_ru": "Мастер словарного запаса",
            "description": "Learn 200 new words",
            "description_ru": "Выучите 200 новых слов",
            "category": "vocabulary",
            "requirement_type": "words_learned",
            "requirement_value": 200,
            "xp_bonus": 400,
            "icon": "📖"
        },
        # Streak achievements
        {
            "name": "Consistent Learner",
            "name_ru": "Последовательный ученик",
            "description": "Maintain a 7-day streak",
            "description_ru": "Сохраняйте серию 7 дней",
            "category": "streak",
            "requirement_type": "streak_days",
            "requirement_value": 7,
            "xp_bonus": 100,
            "icon": "🔥"
        },
        {
            "name": "Unstoppable",
            "name_ru": "Неудержимый",
            "description": "Maintain a 30-day streak",
            "description_ru": "Сохраняйте серию 30 дней",
            "category": "streak",
            "requirement_type": "streak_days",
            "requirement_value": 30,
            "xp_bonus": 500,
            "icon": "⚡"
        },
        # Game achievements
        {
            "name": "Game Enthusiast",
            "name_ru": "Любитель игр",
            "description": "Play 20 games",
            "description_ru": "Сыграйте 20 игр",
            "category": "games",
            "requirement_type": "games_played",
            "requirement_value": 20,
            "xp_bonus": 150,
            "icon": "🎮"
        },
        # Perfect score achievements
        {
            "name": "Perfectionist",
            "name_ru": "Перфекционист",
            "description": "Get 10 perfect scores",
            "description_ru": "Получите 10 идеальных результатов",
            "category": "mastery",
            "requirement_type": "perfect_scores",
            "requirement_value": 10,
            "xp_bonus": 300,
            "icon": "⭐"
        },
    ]
    
    @classmethod
    async def check_achievements(
        cls,
        db: AsyncSession,
        user_id: str,
        stats: Dict[str, int]
    ) -> List[UserAchievement]:
        """Check and award achievements based on user stats"""
        new_achievements = []
        
        # Get existing achievements
        result = await db.execute(
            select(UserAchievement.achievement_id).where(
                UserAchievement.user_id == user_id
            )
        )
        existing_ids = [row[0] for row in result.fetchall()]
        
        for achievement_data in cls.ACHIEVEMENTS:
            # Check if already earned
            result = await db.execute(
                select(Achievement).where(Achievement.name == achievement_data["name"])
            )
            achievement = result.scalar_one_or_none()
            
            if achievement is None:
                # Create achievement if not exists
                achievement = Achievement(**achievement_data)
                db.add(achievement)
                await db.flush()
            
            if achievement.id in existing_ids:
                continue
            
            # Check requirement
            req_type = achievement.requirement_type
            req_value = achievement.requirement_value
            
            if stats.get(req_type, 0) >= req_value:
                user_achievement = UserAchievement(
                    user_id=user_id,
                    achievement_id=achievement.id
                )
                db.add(user_achievement)
                new_achievements.append(user_achievement)
        
        await db.commit()
        return new_achievements
    
    @classmethod
    async def get_user_achievements(
        cls,
        db: AsyncSession,
        user_id: str
    ) -> List[Dict[str, Any]]:
        """Get all achievements with earned status"""
        result = await db.execute(
            select(Achievement)
        )
        all_achievements = result.scalars().all()
        
        result = await db.execute(
            select(UserAchievement).where(UserAchievement.user_id == user_id)
        )
        earned = {ua.achievement_id: ua for ua in result.scalars().all()}
        
        achievements = []
        for achievement in all_achievements:
            achievement_dict = {
                "id": achievement.id,
                "name": achievement.name,
                "description": achievement.description,
                "category": achievement.category,
                "icon": achievement.icon_url,
                "xp_bonus": achievement.xp_bonus,
                "earned": achievement.id in earned,
                "earned_at": earned[achievement.id].unlocked_at if achievement.id in earned else None
            }
            achievements.append(achievement_dict)
        
        return achievements


class DailyGoalService:
    """Service for managing daily learning goals"""
    
    @staticmethod
    async def get_or_create_daily_goal(
        db: AsyncSession,
        user_id: str,
        goal_date: date = None
    ) -> DailyGoal:
        """Get or create daily goal for a specific date"""
        if goal_date is None:
            goal_date = date.today()
        
        result = await db.execute(
            select(DailyGoal).where(
                and_(
                    DailyGoal.user_id == user_id,
                    DailyGoal.goal_date == goal_date
                )
            )
        )
        goal = result.scalar_one_or_none()
        
        if goal is None:
            goal = DailyGoal(
                user_id=user_id,
                goal_date=goal_date
            )
            db.add(goal)
            await db.commit()
            await db.refresh(goal)
        
        return goal
    
    @staticmethod
    async def update_goal_progress(
        db: AsyncSession,
        user_id: str,
        lessons_completed: int = 0,
        words_learned: int = 0,
        minutes_spent: int = 0,
        xp_earned: int = 0
    ) -> DailyGoal:
        """Update daily goal progress"""
        goal = await DailyGoalService.get_or_create_daily_goal(db, user_id)
        
        goal.lessons_completed += lessons_completed
        goal.words_learned += words_learned
        goal.minutes_spent += minutes_spent
        goal.xp_earned += xp_earned
        
        # Check if goal is completed
        if (goal.lessons_completed >= goal.lessons_target and
            goal.words_learned >= goal.words_target and
            goal.minutes_spent >= goal.minutes_target):
            goal.is_completed = True
        
        await db.commit()
        await db.refresh(goal)
        return goal
    
    @staticmethod
    async def get_weekly_progress(
        db: AsyncSession,
        user_id: str
    ) -> List[Dict[str, Any]]:
        """Get progress for the current week"""
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        
        weekly_data = []
        for i in range(7):
            day = week_start + timedelta(days=i)
            result = await db.execute(
                select(DailyGoal).where(
                    and_(
                        DailyGoal.user_id == user_id,
                        DailyGoal.goal_date == day
                    )
                )
            )
            goal = result.scalar_one_or_none()
            
            weekly_data.append({
                "date": day,
                "completed": goal.is_completed if goal else False,
                "lessons": goal.lessons_completed if goal else 0,
                "words": goal.words_learned if goal else 0,
                "minutes": goal.minutes_spent if goal else 0,
                "xp": goal.xp_earned if goal else 0
            })
        
        return weekly_data


class RewardService:
    """Service for managing rewards (avatars, badges, themes)"""
    
    # Reward definitions
    REWARDS = {
        "avatars": [
            {"id": "owl", "name": "Professor Hoot", "icon": "🦉", "level_required": 1},
            {"id": "fox", "name": "Felix Fox", "icon": "🦊", "level_required": 3},
            {"id": "rabbit", "name": "Ruby Rabbit", "icon": "🐰", "level_required": 5},
            {"id": "bear", "name": "Bruno Bear", "icon": "🐻", "level_required": 7},
            {"id": "panda", "name": "Ping Panda", "icon": "🐼", "level_required": 10},
            {"id": "unicorn", "name": "Sparkle Unicorn", "icon": "🦄", "level_required": 15},
        ],
        "themes": [
            {"id": "default", "name": "Classic", "colors": {"primary": "#6C63FF"}},
            {"id": "ocean", "name": "Ocean", "colors": {"primary": "#00BCD4"}, "level_required": 5},
            {"id": "forest", "name": "Forest", "colors": {"primary": "#4CAF50"}, "level_required": 8},
            {"id": "sunset", "name": "Sunset", "colors": {"primary": "#FF5722"}, "level_required": 12},
        ],
        "stickers": [
            {"id": "star", "name": "Star", "icon": "⭐", "achievement": "First Steps"},
            {"id": "fire", "name": "On Fire", "icon": "🔥", "achievement": "Consistent Learner"},
            {"id": "trophy", "name": "Champion", "icon": "🏆", "achievement": "Scholar"},
        ]
    }
    
    @classmethod
    async def check_and_award_rewards(
        cls,
        db: AsyncSession,
        user_id: str,
        level: int
    ) -> List[Reward]:
        """Check and award rewards based on level"""
        new_rewards = []
        
        # Check avatar rewards
        for avatar in cls.REWARDS["avatars"]:
            if level >= avatar["level_required"]:
                # Check if already earned
                result = await db.execute(
                    select(Reward).where(
                        and_(
                            Reward.user_id == user_id,
                            Reward.reward_type == "avatar",
                            Reward.reward_data["id"].astext == avatar["id"]
                        )
                    )
                )
                if result.scalar_one_or_none() is None:
                    reward = Reward(
                        user_id=user_id,
                        reward_type="avatar",
                        reward_data=avatar
                    )
                    db.add(reward)
                    new_rewards.append(reward)
        
        # Check theme rewards
        for theme in cls.REWARDS["themes"]:
            if level >= theme.get("level_required", 0):
                result = await db.execute(
                    select(Reward).where(
                        and_(
                            Reward.user_id == user_id,
                            Reward.reward_type == "theme",
                            Reward.reward_data["id"].astext == theme["id"]
                        )
                    )
                )
                if result.scalar_one_or_none() is None:
                    reward = Reward(
                        user_id=user_id,
                        reward_type="theme",
                        reward_data=theme
                    )
                    db.add(reward)
                    new_rewards.append(reward)
        
        if new_rewards:
            await db.commit()
        
        return new_rewards
    
    @classmethod
    async def get_user_rewards(
        cls,
        db: AsyncSession,
        user_id: str
    ) -> Dict[str, List[Dict]]:
        """Get all rewards earned by user"""
        result = await db.execute(
            select(Reward).where(Reward.user_id == user_id)
        )
        rewards = result.scalars().all()
        
        organized = {"avatars": [], "themes": [], "stickers": []}
        for reward in rewards:
            reward_dict = {
                "id": reward.reward_data.get("id"),
                "name": reward.reward_data.get("name"),
                "icon": reward.reward_data.get("icon"),
                "earned_at": reward.earned_at
            }
            if reward.reward_type in organized:
                organized[reward.reward_type].append(reward_dict)
        
        return organized


class GamificationService:
    """Main gamification service combining all features"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.xp_service = XPService()
        self.streak_service = StreakService()
        self.achievement_service = AchievementService()
        self.daily_goal_service = DailyGoalService()
        self.reward_service = RewardService()
    
    async def award_xp(
        self,
        user_id: str,
        xp_amount: int,
        activity_type: str
    ) -> Dict[str, Any]:
        """Award XP and handle level ups, achievements, etc."""
        # Get streak bonus
        streak_bonus = await self.streak_service.get_streak_bonus(self.db, user_id)
        total_xp = int(xp_amount * streak_bonus)
        
        # Update daily goal
        await self.daily_goal_service.update_goal_progress(
            self.db, user_id, xp_earned=total_xp
        )
        
        # Update streak
        await self.streak_service.update_streak(self.db, user_id)
        
        # Get user stats for achievement checking
        stats = await self._get_user_stats(user_id)
        
        # Check achievements
        new_achievements = await self.achievement_service.check_achievements(
            self.db, user_id, stats
        )
        
        # Check level up
        level_info = self.xp_service.get_level_progress(stats.get("total_xp", 0) + total_xp)
        
        # Check rewards
        new_rewards = await self.reward_service.check_and_award_rewards(
            self.db, user_id, level_info["level"]
        )
        
        return {
            "xp_earned": total_xp,
            "streak_bonus": streak_bonus,
            "level_info": level_info,
            "new_achievements": new_achievements,
            "new_rewards": new_rewards
        }
    
    async def _get_user_stats(self, user_id: str) -> Dict[str, int]:
        """Get user statistics for achievement checking"""
        # Lessons completed
        result = await self.db.execute(
            select(func.count(UserProgress.id)).where(
                and_(
                    UserProgress.user_id == user_id,
                    UserProgress.status == "completed"
                )
            )
        )
        lessons_completed = result.scalar() or 0
        
        # Words learned
        result = await self.db.execute(
            select(func.count(VocabularyProgress.id)).where(
                and_(
                    VocabularyProgress.user_id == user_id,
                    VocabularyProgress.mastery_level >= 1
                )
            )
        )
        words_learned = result.scalar() or 0
        
        # Streak
        result = await self.db.execute(
            select(Streak).where(Streak.user_id == user_id)
        )
        streak = result.scalar_one_or_none()
        streak_days = streak.current_streak if streak else 0
        
        return {
            "lessons_completed": lessons_completed,
            "words_learned": words_learned,
            "streak_days": streak_days,
            "total_xp": 0  # Would need to track this separately
        }
