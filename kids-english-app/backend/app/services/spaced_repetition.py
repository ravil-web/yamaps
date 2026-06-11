"""
Spaced Repetition Service - SM-2 Algorithm Implementation

The SM-2 algorithm is used to schedule vocabulary reviews at optimal intervals
to maximize retention while minimizing study time.
"""
import math
from datetime import date, timedelta
from typing import Tuple
from app.config import settings


class SpacedRepetitionService:
    """
    Implementation of the SM-2 spaced repetition algorithm.
    
    Quality ratings (0-5):
    0 - Complete blackout (didn't remember at all)
    1 - Incorrect response, but recognized the correct one
    2 - Incorrect response, but the correct one seemed easy to recall
    3 - Correct response with difficulty
    4 - Correct response after some hesitation
    5 - Perfect response (immediate and correct)
    """
    
    MIN_EASE_FACTOR = settings.SM2_MIN_EASE_FACTOR  # 1.3
    DEFAULT_EASE_FACTOR = settings.SM2_DEFAULT_EASE_FACTOR  # 2.5
    EASY_BONUS = settings.SM2_EASY_BONUS  # 1.3
    INTERVAL_MODIFIER = settings.SM2_INTERVAL_MODIFIER  # 1.0
    
    @classmethod
    def calculate_next_review(
        cls,
        quality: int,
        current_ease_factor: float,
        current_interval: int,
        current_repetitions: int
    ) -> Tuple[int, float, int, date]:
        """
        Calculate the next review parameters based on the SM-2 algorithm.
        
        Args:
            quality: Quality of response (0-5)
            current_ease_factor: Current ease factor (typically starts at 2.5)
            current_interval: Current interval in days
            current_repetitions: Number of consecutive correct responses
            
        Returns:
            Tuple of (new_interval, new_ease_factor, new_repetitions, next_review_date)
        """
        # Validate quality rating
        if quality < 0 or quality > 5:
            raise ValueError("Quality must be between 0 and 5")
        
        # Calculate new ease factor
        new_ease_factor = cls._calculate_ease_factor(quality, current_ease_factor)
        
        # Calculate new interval and repetitions
        if quality < 3:
            # Failed - reset repetitions and start over
            new_repetitions = 0
            new_interval = 1  # Start with 1 day
        else:
            # Successful - increase interval
            new_repetitions = current_repetitions + 1
            
            if new_repetitions == 1:
                new_interval = 1
            elif new_repetitions == 2:
                new_interval = 6
            else:
                # For repetitions >= 3, use the formula
                new_interval = math.ceil(current_interval * new_ease_factor * cls.INTERVAL_MODIFIER)
        
        # Apply easy bonus for quality >= 4
        if quality >= 4:
            new_interval = math.ceil(new_interval * cls.EASY_BONUS)
        
        # Calculate next review date
        next_review_date = date.today() + timedelta(days=new_interval)
        
        return new_interval, new_ease_factor, new_repetitions, next_review_date
    
    @classmethod
    def _calculate_ease_factor(cls, quality: int, current_ease_factor: float) -> float:
        """
        Calculate new ease factor based on response quality.
        
        Formula: EF' = EF + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
        """
        new_ease_factor = current_ease_factor + (
            0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)
        )
        
        # Ensure minimum ease factor
        return max(cls.MIN_EASE_FACTOR, new_ease_factor)
    
    @classmethod
    def get_words_for_review(cls, vocabulary_progress_list: list) -> list:
        """
        Filter vocabulary items that are due for review today.
        
        Args:
            vocabulary_progress_list: List of vocabulary progress records
            
        Returns:
            List of vocabulary items due for review
        """
        today = date.today()
        return [
            vp for vp in vocabulary_progress_list
            if vp.next_review_date <= today
        ]
    
    @classmethod
    def calculate_mastery_level(cls, repetitions: int, ease_factor: float, interval: int) -> int:
        """
        Calculate mastery level (0-5) based on repetition history.
        
        This provides a user-friendly representation of learning progress.
        """
        if repetitions == 0:
            return 0
        elif repetitions == 1:
            return 1
        elif repetitions == 2:
            return 2
        elif repetitions >= 3 and interval < 21:
            return 3
        elif repetitions >= 3 and interval < 90:
            return 4
        else:
            return 5
    
    @classmethod
    def get_review_priority(cls, vocabulary_progress) -> float:
        """
        Calculate priority score for review ordering.
        
        Higher priority = more urgent need for review.
        """
        today = date.today()
        days_overdue = (today - vocabulary_progress.next_review_date).days
        
        # Base priority from days overdue
        priority = max(0, days_overdue) * 10
        
        # Adjust for mastery level (lower mastery = higher priority)
        mastery = cls.calculate_mastery_level(
            vocabulary_progress.repetitions,
            float(vocabulary_progress.ease_factor),
            vocabulary_progress.interval_days
        )
        priority += (5 - mastery) * 5
        
        # Adjust for past performance
        if vocabulary_progress.correct_count + vocabulary_progress.incorrect_count > 0:
            accuracy = vocabulary_progress.correct_count / (
                vocabulary_progress.correct_count + vocabulary_progress.incorrect_count
            )
            priority += (1 - accuracy) * 10
        
        return priority


class ReviewScheduler:
    """Service for scheduling and managing reviews"""
    
    @staticmethod
    def get_optimal_review_time(user_id: str) -> list:
        """
        Get optimal review schedule for a user.
        
        Returns list of time slots when reviews should be done.
        """
        # This could be enhanced with user behavior analysis
        # For now, return standard intervals
        return [
            {"time": "09:00", "label": "Morning Review"},
            {"time": "15:00", "label": "Afternoon Review"},
            {"time": "19:00", "label": "Evening Review"},
        ]
    
    @staticmethod
    def estimate_review_time(vocabulary_count: int) -> int:
        """
        Estimate time needed for review in minutes.
        
        Assumes average 30 seconds per word.
        """
        return max(1, vocabulary_count // 2)
    
    @staticmethod
    def get_daily_review_limit(age: int) -> int:
        """
        Get recommended daily review limit based on child's age.
        """
        if age <= 6:
            return 10
        elif age <= 8:
            return 15
        elif age <= 10:
            return 20
        else:
            return 30
