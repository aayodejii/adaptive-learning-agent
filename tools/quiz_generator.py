"""
Tool 2: Structured Quiz Generator
Generates quizzes with validated Pydantic schemas
"""

import json
from typing import Any, Type

from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate

from pydantic import BaseModel, ConfigDict, Field

from models.schemas import Quiz, QuizQuestion


class QuizGeneratorInput(BaseModel):
    """Input schema for Quiz Generator"""

    topic: str = Field(..., description="The topic for the quiz")
    difficulty: str = Field(
        ..., description="Difficulty level: beginner, intermediate, or expert"
    )
    num_questions: int = Field(
        default=5, ge=3, le=10, description="Number of questions to generate"
    )
    module_id: int = Field(default=1, description="Associated module ID")


class StructuredQuizGenerator(BaseTool):
    """
    Custom LangChain tool for generating structured quizzes.

    Uses Pydantic output parser to ensure reliable, validated quiz structure.
    """

    name: str = "structured_quiz_generator"
    description: str = """
    Generates structured quizzes with multiple-choice questions for a given topic.
    
    Use this tool when:
    - User wants to start a quiz or assessment
    - User completes reading a module and is ready to test knowledge
    - You need to assess the user's understanding of a topic
    
    Input:
    - topic: The subject matter (e.g., "Python Functions", "Machine Learning Basics")
    - difficulty: beginner, intermediate, or expert
    - num_questions: How many questions (3-10, default 5)
    
    Returns: A structured quiz with questions, options, correct answers, and explanations.
    """
    args_schema: Type[BaseModel] = QuizGeneratorInput

    llm: Any = Field(default=None, exclude=True)
    parser: Any = Field(default=None, exclude=True)

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def __init__(self):
        super().__init__()
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0.7)
        self.parser = PydanticOutputParser(pydantic_object=Quiz)

    def _run(
        self, topic: str, difficulty: str, num_questions: int = 5, module_id: int = 1
    ) -> str:
        """Generate a structured quiz"""

        try:
            prompt = PromptTemplate(
                template="""You are an expert educational assessment creator.

                Generate a high-quality quiz on the following topic:

                Topic: {topic}
                Difficulty Level: {difficulty}
                Number of Questions: {num_questions}

                Requirements:
                1. Create {num_questions} multiple-choice questions
                2. Each question must have exactly 4 options
                3. Questions should be clear, unambiguous, and test understanding
                4. Include a brief explanation for the correct answer
                5. Ensure difficulty matches the specified level:
                - beginner: Basic concepts and definitions
                - intermediate: Application and analysis
                - expert: Complex problem-solving and synthesis

                {format_instructions}

                Generate the quiz now:""",
                input_variables=["topic", "difficulty", "num_questions"],
                partial_variables={
                    "format_instructions": self.parser.get_format_instructions()
                },
            )

            chain = prompt | self.llm | self.parser

            quiz = chain.invoke(
                {
                    "topic": topic,
                    "difficulty": difficulty,
                    "num_questions": num_questions,
                }
            )

            quiz.module_id = module_id

            return self._format_quiz_output(quiz)

        except Exception as e:
            return f"Error generating quiz: {str(e)}"

    def _format_quiz_output(self, quiz: Quiz) -> str:
        """Format quiz as readable text for the agent"""
        output = [
            f"Quiz Generated Successfully!",
            f"Topic: {quiz.topic}",
            f"Difficulty: {quiz.difficulty}",
            f"Questions: {len(quiz.questions)}\n",
            "=" * 50,
        ]

        for idx, q in enumerate(quiz.questions, 1):
            output.append(f"\nQuestion {idx}: {q.question}")
            for opt_idx, option in enumerate(q.options):
                output.append(f"  {chr(65 + opt_idx)}. {option}")
            output.append(f"Correct Answer: {chr(65 + q.correct_index)}")
            if q.explanation:
                output.append(f"Explanation: {q.explanation}")
            output.append("-" * 50)

        quiz_json = quiz.model_dump_json(indent=2)

        output.append("\n[Quiz data saved in structured format]")
        output.append(f"Quiz JSON:\n{quiz_json}")

        return "\n".join(output)


class QuizEvaluator:
    """Helper class to evaluate quiz answers"""

    @staticmethod
    def evaluate_answers(quiz: Quiz, user_answers: list[int]) -> dict:
        """
        Evaluate user's quiz answers

        Args:
            quiz: The Quiz object
            user_answers: List of user's answer indices (0-3)

        Returns:
            dict with score, feedback, and detailed results
        """
        if len(user_answers) != len(quiz.questions):
            return {
                "error": "Number of answers doesn't match number of questions",
                "score": 0.0,
            }

        results = []
        correct_count = 0

        for idx, (question, user_answer) in enumerate(
            zip(quiz.questions, user_answers)
        ):
            is_correct = user_answer == question.correct_index
            if is_correct:
                correct_count += 1

            results.append(
                {
                    "question_num": idx + 1,
                    "question": question.question,
                    "user_answer": chr(65 + user_answer),
                    "correct_answer": chr(65 + question.correct_index),
                    "is_correct": is_correct,
                    "explanation": question.explanation,
                }
            )

        score = (correct_count / len(quiz.questions)) * 100

        if score >= 90:
            feedback = "Excellent! You've mastered this topic."
        elif score >= 80:
            feedback = "Great work! You have a strong understanding."
        elif score >= 70:
            feedback = "Good job! You're on the right track."
        elif score >= 60:
            feedback = "Fair performance. Review the material and try again."
        else:
            feedback = "More study needed. Don't worry, practice makes perfect!"

        return {
            "score": score,
            "correct": correct_count,
            "total": len(quiz.questions),
            "percentage": f"{score:.1f}%",
            "feedback": feedback,
            "results": results,
        }
