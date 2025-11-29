"""
Demo script to test components without the full UI
Useful for debugging and showcasing individual features
"""

import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent))

from tools.knowledge_manager import KnowledgeProfileManager
from tools.quiz_generator import StructuredQuizGenerator, QuizEvaluator
from tools.resource_search import RealTimeResourceSearch
from models.schemas import Quiz, QuizQuestion
from config import config, check_api_keys


def demo_configuration():
    """Demo 1: Show configuration status"""
    print("=" * 60)
    print("DEMO 1: Configuration Check")
    print("=" * 60)
    print(config.get_display_info())
    print("\n")


def demo_knowledge_manager():
    """Demo 2: Test Knowledge Profile Manager"""
    print("=" * 60)
    print("DEMO 2: Knowledge Profile Manager")
    print("=" * 60)

    manager = KnowledgeProfileManager()

    # Test reading profile
    print("\n1. Reading user profile...")
    result = manager._run(action="read", user_id="demo_user")
    print(result)

    # Test updating profile
    print("\n2. Updating profile with new progress...")
    result = manager._run(
        action="update",
        user_id="demo_user",
        skill="Python Programming",
        module_title="Python Fundamentals",
        score=85.0,
    )
    print(result)

    # Test getting summary
    print("\n3. Getting progress summary...")
    result = manager._run(action="get_summary", user_id="demo_user")
    print(result)
    print("\n")


def demo_quiz_generator():
    """Demo 3: Test Structured Quiz Generator"""
    print("=" * 60)
    print("DEMO 3: Structured Quiz Generator")
    print("=" * 60)

    try:
        check_api_keys()

        generator = StructuredQuizGenerator()

        print("\n1. Generating quiz on 'Python Functions'...")
        result = generator._run(
            topic="Python Functions",
            difficulty="beginner",
            num_questions=3,
            module_id=1,
        )
        print(result)

        # Parse the JSON from result to demonstrate evaluation
        print("\n2. Simulating quiz evaluation...")

        # Create a sample quiz for evaluation demo
        sample_quiz = Quiz(
            module_id=1,
            topic="Python Functions",
            difficulty="beginner",
            questions=[
                QuizQuestion(
                    question="What keyword is used to define a function in Python?",
                    options=["func", "def", "function", "define"],
                    correct_index=1,
                    explanation="The 'def' keyword is used to define functions in Python.",
                ),
                QuizQuestion(
                    question="What does a function return if no return statement is specified?",
                    options=["0", "None", "Empty string", "Error"],
                    correct_index=1,
                    explanation="Functions return None by default when no return statement is present.",
                ),
                QuizQuestion(
                    question="Which of these is correct function call syntax?",
                    options=[
                        "function_name[]",
                        "function_name()",
                        "function_name{}",
                        "call function_name",
                    ],
                    correct_index=1,
                    explanation="Functions are called using parentheses: function_name()",
                ),
            ],
        )

        # Simulate user answers (correct, wrong, correct)
        user_answers = [1, 0, 1]

        evaluator = QuizEvaluator()
        results = evaluator.evaluate_answers(sample_quiz, user_answers)

        print(f"\nQuiz Results:")
        print(f"Score: {results['score']:.1f}%")
        print(f"Correct: {results['correct']}/{results['total']}")
        print(f"Feedback: {results['feedback']}")

    except ValueError as e:
        print(f"\nError: {e}")
        print("Set OPENAI_API_KEY in .env file to test quiz generation")

    print("\n")


def demo_resource_search():
    """Demo 4: Test Resource Search"""
    print("=" * 60)
    print("DEMO 4: Real-Time Resource Search")
    print("=" * 60)

    search = RealTimeResourceSearch()

    print("\n1. Searching for Python tutorials...")
    result = search._run(
        query="Python programming tutorials for beginners", max_results=3
    )
    print(result)
    print("\n")


def demo_full_workflow():
    """Demo 5: Simulate complete learning workflow"""
    print("=" * 60)
    print("DEMO 5: Complete Learning Workflow Simulation")
    print("=" * 60)

    user_id = "workflow_demo_user"
    skill = "Machine Learning"

    # Step 1: Initialize user profile
    print("\nStep 1: Initialize learning path")
    print(f"User: {user_id}")
    print(f"Target Skill: {skill}")

    manager = KnowledgeProfileManager()
    profile = manager._run(action="read", user_id=user_id)
    print(profile)

    # Step 2: Find resources
    print("\nStep 2: Find learning resources")
    search = RealTimeResourceSearch()
    resources = search._run(query=f"{skill} beginner tutorial", max_results=3)
    print(resources[:300] + "...")  # Truncate for readability

    # Step 3: Take quiz
    print("\nStep 3: Take assessment quiz")
    print("(Simulating quiz completion with 85% score)")

    # Step 4: Update progress
    print("\nStep 4: Update learning progress")
    update_result = manager._run(
        action="update",
        user_id=user_id,
        skill=skill,
        module_title="ML Fundamentals",
        score=85.0,
    )
    print(update_result)

    # Step 5: Check progress
    print("\nStep 5: View progress summary")
    summary = manager._run(action="get_summary", user_id=user_id)
    print(summary)

    print("\nWorkflow complete!")
    print("\n")


def demo_pydantic_schemas():
    """Demo 6: Show Pydantic schema validation"""
    print("=" * 60)
    print("DEMO 6: Pydantic Schema Validation")
    print("=" * 60)

    from models.schemas import Module, LearningPlan, ModuleStatus
    from datetime import datetime

    print("\n1. Creating a valid module...")
    try:
        module = Module(
            id=1,
            title="Introduction to Python",
            status=ModuleStatus.ACTIVE,
            topics=["Variables", "Data Types", "Control Flow"],
            estimated_hours=5,
            mastery_score=0.0,
        )
        print("Valid module created:")
        print(f"  {module.model_dump_json(indent=2)}")
    except Exception as e:
        print(f"Error: {e}")

    print("\n2. Testing validation with invalid data...")
    try:
        invalid_module = Module(
            id=1, title="Test Module", mastery_score=150.0  # Invalid: should be 0-100
        )
    except Exception as e:
        print(f"Validation caught error: {type(e).__name__}")
        print(f"  {str(e)[:100]}...")

    print("\n3. Creating a learning plan...")
    plan = LearningPlan(
        skill="Data Science",
        level="intermediate",
        modules=[module],
        created=datetime.now(),
    )
    print("Learning plan created successfully")
    print(f"  Active module: {plan.get_active_module().title}")

    print("\n")


def demo_agent_reasoning():
    """Demo 7: Show how tool-calling agent processes a task"""
    print("=" * 60)
    print("DEMO 7: Tool-Calling Agent Process Simulation")
    print("=" * 60)

    print("\nUser Query: 'I want to start learning Python'")
    print("\n--- Agent Tool-Calling Process ---\n")

    print("Step 1: Agent analyzes user intent")
    print("   Decision: User wants to start learning Python")
    print("   Planning: Check progress, find resources, offer assessment")

    print("\nStep 2: Tool Call - knowledge_profile_manager")
    print("   Input: {action: 'read', user_id: 'user123'}")
    print("   Result: User is new, no existing progress")

    print("\nStep 3: Tool Call - real_time_resource_search")
    print("   Input: {query: 'Python programming beginner tutorial', max_results: 5}")
    print("   Result: Found 5 relevant resources including Python.org docs")

    print("\nStep 4: Tool Call - structured_quiz_generator")
    print(
        "   Input: {topic: 'Python Basics', difficulty: 'beginner', num_questions: 5}"
    )
    print("   Result: Quiz generated with 5 questions")

    print("\nStep 5: Agent synthesizes response")
    print("   Final Answer: 'Welcome! I've found some great Python resources...")
    print("   Would you like to start with a beginner quiz to assess your level?'")

    print("\n")


def interactive_menu():
    """Interactive demo menu"""
    while True:
        print("\n" + "=" * 60)
        print("Demo & Testing Menu")
        print("=" * 60)
        print("\n1. Configuration Check")
        print("2. Test Knowledge Profile Manager")
        print("3. Test Quiz Generator (requires API key)")
        print("4. Test Resource Search")
        print("5. Full Workflow Simulation")
        print("6. Pydantic Schema Validation")
        print("7. Tool-Calling Agent Process Simulation")
        print("8. Run All Demos")
        print("0. Exit")

        choice = input("\nSelect demo (0-8): ").strip()

        if choice == "0":
            print("\nGoodbye!")
            break
        elif choice == "1":
            demo_configuration()
        elif choice == "2":
            demo_knowledge_manager()
        elif choice == "3":
            demo_quiz_generator()
        elif choice == "4":
            demo_resource_search()
        elif choice == "5":
            demo_full_workflow()
        elif choice == "6":
            demo_pydantic_schemas()
        elif choice == "7":
            demo_agent_reasoning()
        elif choice == "8":
            print("\n Running all demos...\n")
            demo_configuration()
            input("Press Enter to continue...")
            demo_pydantic_schemas()
            input("Press Enter to continue...")
            demo_knowledge_manager()
            input("Press Enter to continue...")
            demo_resource_search()
            input("Press Enter to continue...")
            demo_agent_reasoning()
            input("Press Enter to continue...")
            demo_full_workflow()
            print("\n All demos complete!")
        else:
            print("Invalid choice. Please select 0-8.")

        if choice != "0" and choice != "8":
            input("\nPress Enter to return to menu...")


if __name__ == "__main__":
    print("\n Component Testing & Demo")
    print("=" * 60)
    print("\nThis script demonstrates individual components of the")
    print("Personalized Learning Path Generator Agent.")
    print("\nNote: Some demos require OPENAI_API_KEY in .env file")
    print("=" * 60)

    interactive_menu()
