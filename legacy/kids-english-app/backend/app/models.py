"""
Database models for the Kids English Learning App
"""
import uuid
from datetime import date, datetime
from typing import Optional, List
from sqlalchemy import (
    Boolean, Date, DateTime, Integer, String, Text, 
    ForeignKey, Numeric, JSON, UniqueConstraint, Index
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class User(Base):
    """User model for children, parents, and admins"""
    __tablename__ = "users"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True)
    password_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="child")  # child, parent, admin
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    date_of_birth: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    language_preference: Mapped[str] = mapped_column(String(10), default="ru")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    children: Mapped[List["ParentChildRelation"]] = relationship(
        "ParentChildRelation", foreign_keys="ParentChildRelation.parent_id", back_populates="parent"
    )
    parents: Mapped[List["ParentChildRelation"]] = relationship(
        "ParentChildRelation", foreign_keys="ParentChildRelation.child_id", back_populates="child"
    )
    progress: Mapped[List["UserProgress"]] = relationship("UserProgress", back_populates="user")
    vocabulary_progress: Mapped[List["VocabularyProgress"]] = relationship("VocabularyProgress", back_populates="user")
    achievements: Mapped[List["UserAchievement"]] = relationship("UserAchievement", back_populates="user")
    game_sessions: Mapped[List["GameSession"]] = relationship("GameSession", back_populates="user")
    streak: Mapped[Optional["Streak"]] = relationship("Streak", back_populates="user", uselist=False)
    daily_goals: Mapped[List["DailyGoal"]] = relationship("DailyGoal", back_populates="user")
    activity_logs: Mapped[List["ActivityLog"]] = relationship("ActivityLog", back_populates="user")
    rewards: Mapped[List["Reward"]] = relationship("Reward", back_populates="user")
    test_results: Mapped[List["TestResult"]] = relationship("TestResult", back_populates="user")


class ParentChildRelation(Base):
    """Relationship between parent and child accounts"""
    __tablename__ = "parent_child_relations"
    __table_args__ = (UniqueConstraint("parent_id", "child_id"),)
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    parent_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    child_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    relationship: Mapped[str] = mapped_column(String(20), default="parent")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    parent: Mapped["User"] = relationship("User", foreign_keys=[parent_id], back_populates="children")
    child: Mapped["User"] = relationship("User", foreign_keys=[child_id], back_populates="parents")


class Category(Base):
    """Lesson categories"""
    __tablename__ = "categories"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    name_en: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    icon_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    color: Mapped[str] = mapped_column(String(7), default="#4CAF50")
    order_index: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Relationships
    lessons: Mapped[List["Lesson"]] = relationship("Lesson", back_populates="category")


class Lesson(Base):
    """Learning lessons"""
    __tablename__ = "lessons"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    category_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("categories.id"))
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    title_en: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    difficulty_level: Mapped[int] = mapped_column(Integer, default=1)  # 1-5
    order_index: Mapped[int] = mapped_column(Integer, default=0)
    estimated_minutes: Mapped[int] = mapped_column(Integer, default=15)
    xp_reward: Mapped[int] = mapped_column(Integer, default=100)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    category: Mapped[Optional["Category"]] = relationship("Category", back_populates="lessons")
    vocabulary_items: Mapped[List["VocabularyItem"]] = relationship("VocabularyItem", back_populates="lesson")
    user_progress: Mapped[List["UserProgress"]] = relationship("UserProgress", back_populates="lesson")


class VocabularyItem(Base):
    """Vocabulary words and phrases"""
    __tablename__ = "vocabulary_items"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lesson_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("lessons.id", ondelete="CASCADE"))
    word: Mapped[str] = mapped_column(String(100), nullable=False)
    translation: Mapped[str] = mapped_column(String(200), nullable=False)
    pronunciation: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    audio_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    example_sentence: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    example_translation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    difficulty_level: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    lesson: Mapped[Optional["Lesson"]] = relationship("Lesson", back_populates="vocabulary_items")
    user_progress: Mapped[List["VocabularyProgress"]] = relationship("VocabularyProgress", back_populates="vocabulary")


class UserProgress(Base):
    """User progress on lessons"""
    __tablename__ = "user_progress"
    __table_args__ = (UniqueConstraint("user_id", "lesson_id"),)
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    lesson_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("lessons.id"))
    status: Mapped[str] = mapped_column(String(20), default="not_started")  # not_started, in_progress, completed
    score: Mapped[int] = mapped_column(Integer, default=0)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    time_spent_seconds: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_accessed: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="progress")
    lesson: Mapped["Lesson"] = relationship("Lesson", back_populates="user_progress")


class VocabularyProgress(Base):
    """User progress on vocabulary items with spaced repetition"""
    __tablename__ = "vocabulary_progress"
    __table_args__ = (UniqueConstraint("user_id", "vocabulary_id"),)
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    vocabulary_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("vocabulary_items.id", ondelete="CASCADE"))
    mastery_level: Mapped[int] = mapped_column(Integer, default=0)  # 0-5 (SM-2 algorithm)
    ease_factor: Mapped[float] = mapped_column(Numeric(4, 2), default=2.5)
    interval_days: Mapped[int] = mapped_column(Integer, default=0)
    repetitions: Mapped[int] = mapped_column(Integer, default=0)
    next_review_date: Mapped[date] = mapped_column(Date, default=date.today)
    last_review_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    correct_count: Mapped[int] = mapped_column(Integer, default=0)
    incorrect_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="vocabulary_progress")
    vocabulary: Mapped["VocabularyItem"] = relationship("VocabularyItem", back_populates="user_progress")


class Game(Base):
    """Game definitions"""
    __tablename__ = "games"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    game_type: Mapped[str] = mapped_column(String(50), nullable=False)  # matching, quiz, memory, spelling, etc.
    difficulty_levels: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    config: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Relationships
    sessions: Mapped[List["GameSession"]] = relationship("GameSession", back_populates="game")


class GameSession(Base):
    """Game session records"""
    __tablename__ = "game_sessions"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    game_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("games.id"))
    lesson_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("lessons.id"), nullable=True)
    score: Mapped[int] = mapped_column(Integer, default=0)
    max_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    time_spent_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    correct_answers: Mapped[int] = mapped_column(Integer, default=0)
    total_questions: Mapped[int] = mapped_column(Integer, default=0)
    difficulty_level: Mapped[int] = mapped_column(Integer, default=1)
    played_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="game_sessions")
    game: Mapped["Game"] = relationship("Game", back_populates="sessions")


class Achievement(Base):
    """Achievement definitions"""
    __tablename__ = "achievements"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    icon_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    category: Mapped[str] = mapped_column(String(50))  # learning, streak, social, mastery
    requirement_type: Mapped[str] = mapped_column(String(50))  # lessons_completed, words_learned, streak_days
    requirement_value: Mapped[int] = mapped_column(Integer)
    xp_bonus: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Relationships
    user_achievements: Mapped[List["UserAchievement"]] = relationship("UserAchievement", back_populates="achievement")


class UserAchievement(Base):
    """User unlocked achievements"""
    __tablename__ = "user_achievements"
    __table_args__ = (UniqueConstraint("user_id", "achievement_id"),)
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    achievement_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("achievements.id"))
    unlocked_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="achievements")
    achievement: Mapped["Achievement"] = relationship("Achievement", back_populates="user_achievements")


class Reward(Base):
    """User rewards (avatars, badges, stickers, themes)"""
    __tablename__ = "rewards"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    reward_type: Mapped[str] = mapped_column(String(50))  # avatar, badge, sticker, theme
    reward_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    earned_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="rewards")


class DailyGoal(Base):
    """Daily learning goals"""
    __tablename__ = "daily_goals"
    __table_args__ = (UniqueConstraint("user_id", "goal_date"),)
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    goal_date: Mapped[date] = mapped_column(Date, default=date.today)
    lessons_target: Mapped[int] = mapped_column(Integer, default=2)
    lessons_completed: Mapped[int] = mapped_column(Integer, default=0)
    words_target: Mapped[int] = mapped_column(Integer, default=10)
    words_learned: Mapped[int] = mapped_column(Integer, default=0)
    minutes_target: Mapped[int] = mapped_column(Integer, default=15)
    minutes_spent: Mapped[int] = mapped_column(Integer, default=0)
    xp_earned: Mapped[int] = mapped_column(Integer, default=0)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="daily_goals")


class Streak(Base):
    """User learning streaks"""
    __tablename__ = "streaks"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    current_streak: Mapped[int] = mapped_column(Integer, default=0)
    longest_streak: Mapped[int] = mapped_column(Integer, default=0)
    last_activity_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="streak")


class Test(Base):
    """Tests and assessments"""
    __tablename__ = "tests"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    test_type: Mapped[str] = mapped_column(String(50))  # placement, lesson, final
    difficulty_level: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    time_limit_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    passing_score: Mapped[int] = mapped_column(Integer, default=70)
    questions: Mapped[dict] = mapped_column(JSONB, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Relationships
    results: Mapped[List["TestResult"]] = relationship("TestResult", back_populates="test")


class TestResult(Base):
    """Test results"""
    __tablename__ = "test_results"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    test_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tests.id"))
    score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    total_questions: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    correct_answers: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    time_spent_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    answers: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="test_results")
    test: Mapped["Test"] = relationship("Test", back_populates="results")


class ParentSettings(Base):
    """Parent account settings"""
    __tablename__ = "parent_settings"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    parent_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    daily_time_limit_minutes: Mapped[int] = mapped_column(Integer, default=60)
    weekly_reports_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    email_notifications: Mapped[bool] = mapped_column(Boolean, default=True)
    push_notifications: Mapped[bool] = mapped_column(Boolean, default=True)
    content_restrictions: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)


class ActivityLog(Base):
    """User activity logs for analytics"""
    __tablename__ = "activity_logs"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    activity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    activity_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="activity_logs")
    
    # Indexes
    __table_args__ = (
        Index("idx_activity_logs_user", "user_id"),
        Index("idx_activity_logs_date", "created_at"),
    )
