from typing import List, Optional
from enum import Enum
from datetime import datetime

from pydantic import BaseModel, Field


class ModuleStatus(str, Enum):
    """Enum for module completion status"""

    LOCKED = "locked"
    ACTIVE = "active"
    COMPLETED = "completed"


class Module(BaseModel):
    """Individual learning module"""

    id: int = Field(..., description="Unique module identifier")
    title: str = Field(..., description="Module title")
    status: ModuleStatus = Field(default=ModuleStatus.LOCKED)
    topics: List[str] = Field(
        default_factory=list, description="List of topics covered"
    )
    estimated_hours: int = Field(default=4, ge=1, le=20)
    mastery_score: float = Field(default=0.0, ge=0.0, le=100.0)

    class Config:
        use_enum_values = True


class LearningPlan(BaseModel):
    """Complete learning path structure"""

    skill: str = Field(..., description="Target skill to master")
    level: str = Field(..., description="Starting level: beginner/intermediate/expert")
    modules: List[Module] = Field(..., description="Ordered list of learning modules")
    created: datetime = Field(default_factory=datetime.now)

    def get_active_module(self) -> Optional[Module]:
        """Get the currently active module"""
        for module in self.modules:
            if module.status == ModuleStatus.ACTIVE:
                return module
        return None

    def complete_module(self, module_id: int, score: float):
        """Mark a module as completed and unlock the next one"""
        for idx, module in enumerate(self.modules):
            if module.id == module_id:
                module.status = ModuleStatus.COMPLETED
                module.mastery_score = score

                # Unlock next module
                if idx + 1 < len(self.modules):
                    self.modules[idx + 1].status = ModuleStatus.ACTIVE
                break


class QuizQuestion(BaseModel):
    """Single quiz question with multiple choice options"""

    question: str = Field(..., description="The question text")
    options: List[str] = Field(
        ..., min_items=2, max_items=4, description="Answer options"
    )
    correct_index: int = Field(
        ..., ge=0, lt=4, description="Index of correct answer (0-3)"
    )
    explanation: Optional[str] = Field(
        None, description="Explanation of the correct answer"
    )


class Quiz(BaseModel):
    """Structured quiz with multiple questions"""

    module_id: int = Field(..., description="Associated module ID")
    topic: str = Field(..., description="Quiz topic")
    difficulty: str = Field(..., description="beginner/intermediate/expert")
    questions: List[QuizQuestion] = Field(..., min_items=3, max_items=10)

    def calculate_score(self, user_answers: List[int]) -> float:
        """Calculate quiz score as percentage"""
        if not user_answers or len(user_answers) != len(self.questions):
            return 0.0

        correct = sum(
            1
            for i, answer in enumerate(user_answers)
            if answer == self.questions[i].correct_index
        )

        return (correct / len(self.questions)) * 100.0


class ResourceLink(BaseModel):
    """External learning resource"""

    title: str = Field(..., description="Resource title")
    url: str = Field(..., description="Resource URL")
    description: Optional[str] = Field(None, description="Brief description")
    relevance_score: float = Field(default=1.0, ge=0.0, le=1.0)


class ResourceSearchResult(BaseModel):
    """Result from resource search tool"""

    query: str = Field(..., description="Original search query")
    resources: List[ResourceLink] = Field(..., max_items=5)
    search_timestamp: datetime = Field(default_factory=datetime.now)


class UserProfile(BaseModel):
    """User's learning profile and progress"""

    user_id: str = Field(..., description="Unique user identifier")
    skills: dict[str, dict] = Field(
        default_factory=dict,
        description="Dict of skill -> {modules: List, avg_score: float}",
    )
    total_modules_completed: int = Field(default=0)
    overall_avg_score: float = Field(default=0.0)
    last_updated: datetime = Field(default_factory=datetime.now)

    def update_skill_progress(self, skill: str, module_title: str, score: float):
        """Update progress for a specific skill"""
        if skill not in self.skills:
            self.skills[skill] = {"modules": [], "avg_score": 0.0}

        self.skills[skill]["modules"].append(
            {
                "title": module_title,
                "score": score,
                "completed_at": datetime.now().isoformat(),
            }
        )

        # Recalculate average
        scores = [m["score"] for m in self.skills[skill]["modules"]]
        self.skills[skill]["avg_score"] = sum(scores) / len(scores)

        self.total_modules_completed += 1
        self.last_updated = datetime.now()

        # Update overall average
        all_scores = []
        for skill_data in self.skills.values():
            all_scores.extend([m["score"] for m in skill_data["modules"]])

        if all_scores:
            self.overall_avg_score = sum(all_scores) / len(all_scores)
