"""
Tool 1: Knowledge Profile Manager
Manages persistent user state and learning progress
"""

import os
import json
from pathlib import Path

from langchain_core.tools import BaseTool
from typing import Optional, Type
from pydantic import BaseModel, Field, ConfigDict

from models.schemas import UserProfile


class KnowledgeProfileInput(BaseModel):
    """Input schema for Knowledge Profile Manager"""

    action: str = Field(
        ..., description="Action to perform: 'read', 'update', or 'get_summary'"
    )
    user_id: str = Field(default="default_user", description="User identifier")
    skill: Optional[str] = Field(None, description="Skill name for updates")
    module_title: Optional[str] = Field(None, description="Module title")
    score: Optional[float] = Field(None, description="Mastery score (0-100)")


class KnowledgeProfileManager(BaseTool):
    """
    Custom LangChain tool for managing user learning profiles.

    Capabilities:
    - Read user profile from persistent storage
    - Update progress when modules are completed
    - Generate progress summaries
    """

    name: str = "knowledge_profile_manager"
    description: str = """
    Manages user learning progress and state. Use this tool to:
    - Read the user's current learning profile (action='read')
    - Update progress after completing a module (action='update', requires skill, module_title, score)
    - Get a summary of the user's overall progress (action='get_summary')
    
    Always use this tool before generating a quiz to check current progress.
    """
    args_schema: Type[BaseModel] = KnowledgeProfileInput

    storage_path: Path = Field(default_factory=lambda: Path("data/user_profiles"))

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def __init__(self):
        super().__init__()
        self.storage_path = Path("data/user_profiles")
        self.storage_path.mkdir(parents=True, exist_ok=True)

    def _get_profile_path(self, user_id: str) -> Path:
        """Get the file path for a user's profile"""
        return self.storage_path / f"{user_id}.json"

    def _load_profile(self, user_id: str) -> UserProfile:
        """Load user profile from storage"""
        profile_path = self._get_profile_path(user_id)

        if profile_path.exists():
            with open(profile_path, "r") as f:
                data = json.load(f)
                return UserProfile(**data)
        else:
            return UserProfile(user_id=user_id)

    def _save_profile(self, profile: UserProfile):
        """Save user profile to storage"""
        profile_path = self._get_profile_path(profile.user_id)

        with open(profile_path, "w") as f:
            json.dump(profile.model_dump(), f, indent=2, default=str)

    def _run(
        self,
        action: str,
        user_id: str = "default_user",
        skill: Optional[str] = None,
        module_title: Optional[str] = None,
        score: Optional[float] = None,
    ) -> str:
        """Execute the knowledge management action"""

        try:
            profile = self._load_profile(user_id)

            if action == "read":
                return self._format_profile_read(profile)

            elif action == "update":
                if not all([skill, module_title, score is not None]):
                    return (
                        "Error: update action requires skill, module_title, and score"
                    )

                profile.update_skill_progress(skill, module_title, score)
                self._save_profile(profile)

                return f"""Profile updated successfully!
                Module: {module_title}
                Score: {score:.1f}%
                Total modules completed: {profile.total_modules_completed}
                Overall average: {profile.overall_avg_score:.1f}%"""

            elif action == "get_summary":
                return self._format_summary(profile)

            else:
                return f"Error: Unknown action '{action}'. Use 'read', 'update', or 'get_summary'"

        except Exception as e:
            return f"Error managing knowledge profile: {str(e)}"

    def _format_profile_read(self, profile: UserProfile) -> str:
        """Format profile data for reading"""
        if not profile.skills:
            return "No learning history found for this user. This is a new learner!"

        output = [f"User Profile: {profile.user_id}"]
        output.append(f"Total Modules Completed: {profile.total_modules_completed}")
        output.append(f"Overall Average Score: {profile.overall_avg_score:.1f}%\n")

        for skill, data in profile.skills.items():
            output.append(f"Skill: {skill}")
            output.append(f"  Average Score: {data['avg_score']:.1f}%")
            output.append(f"  Modules Completed: {len(data['modules'])}")

            for module in data["modules"][-3:]:
                output.append(f"    - {module['title']}: {module['score']:.1f}%")

        return "\n".join(output)

    def _format_summary(self, profile: UserProfile) -> str:
        """Format a brief summary"""
        if not profile.skills:
            return "No progress yet. Let's start learning!"

        total_skills = len(profile.skills)
        best_skill = max(profile.skills.items(), key=lambda x: x[1]["avg_score"])

        return f"""Progress Summary:
        Skills in progress: {total_skills}
        Total modules completed: {profile.total_modules_completed}
        Overall average: {profile.overall_avg_score:.1f}%
        Best skill: {best_skill[0]} ({best_skill[1]['avg_score']:.1f}%)"""
