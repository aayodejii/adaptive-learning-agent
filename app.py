import json
from datetime import datetime
from typing import List, Dict, Optional

import streamlit as st

from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain_core.callbacks.base import BaseCallbackHandler
from tools.knowledge_manager import KnowledgeProfileManager
from tools.quiz_generator import StructuredQuizGenerator
from tools.resource_search import RealTimeResourceSearch
from models.schemas import LearningPlan, Module, ModuleStatus
from config import config


class StreamlitCallbackHandler(BaseCallbackHandler):
    def __init__(self):
        self.trace_log = []

    def on_tool_start(self, serialized, input_str, **kwargs):
        self.trace_log.append(
            {
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "type": "tool_start",
                "tool": serialized.get("name", "unknown"),
                "input": str(input_str)[:200],
            }
        )

    def on_tool_end(self, output, **kwargs):
        if self.trace_log:
            self.trace_log[-1]["output"] = str(output)[:200]


st.set_page_config(
    page_title="PLPGA - AI Learning Assistant", page_icon="", layout="wide"
)

if "messages" not in st.session_state:
    st.session_state.messages = []
if "learning_plan" not in st.session_state:
    st.session_state.learning_plan = None
if "agent" not in st.session_state:
    st.session_state.agent = None
if "callback_handler" not in st.session_state:
    st.session_state.callback_handler = StreamlitCallbackHandler()
if "current_module_idx" not in st.session_state:
    st.session_state.current_module_idx = 0
if "quiz_state" not in st.session_state:
    st.session_state.quiz_state = None


@st.cache_resource
def initialize_tools():
    knowledge_manager = KnowledgeProfileManager()
    quiz_generator = StructuredQuizGenerator()
    resource_search = RealTimeResourceSearch()
    return [knowledge_manager, quiz_generator, resource_search]


def initialize_agent(target_skill: str, starting_level: str):
    tools = initialize_tools()

    llm = ChatOpenAI(
        model="gpt-4o", api_key=config.OPENAI_API_KEY, temperature=0.7, streaming=True
    )

    system_prompt = f"""You are an adaptive learning assistant helping users master {target_skill} at the {starting_level} level.

Your role:
1. Guide users through their learning journey
2. Use tools to check their progress, generate quizzes, and find resources
3. Remember the conversation history and context
4. Provide clear, encouraging, and accurate responses

When generating quizzes:
- Use the structured_quiz_generator tool
- Present questions clearly
- When evaluating answers, compare them to the exact questions you generated
- Keep track of which questions were asked and answered

You have access to these tools:
- knowledge_profile_manager: Track user progress
- structured_quiz_generator: Create assessments
- real_time_resource_search: Find learning materials

Be supportive and help users achieve their learning goals!"""

    agent = create_agent(
        model=llm,
        tools=tools,
        system_prompt=system_prompt,
    )

    return agent


def generate_learning_plan(target_skill: str, starting_level: str) -> LearningPlan:
    modules = []

    if starting_level == "beginner":
        module_titles = [
            f"Foundations of {target_skill}",
            f"Core Concepts in {target_skill}",
            f"Practical Applications of {target_skill}",
        ]
    elif starting_level == "intermediate":
        module_titles = [
            f"Advanced Concepts in {target_skill}",
            f"Real-World {target_skill} Projects",
            f"Mastering {target_skill}",
        ]
    else:
        module_titles = [
            f"Expert-Level {target_skill}",
            f"Cutting-Edge {target_skill} Research",
            f"{target_skill} Innovation & Leadership",
        ]

    for idx, title in enumerate(module_titles):
        modules.append(
            Module(
                id=idx + 1,
                title=title,
                status=ModuleStatus.ACTIVE if idx == 0 else ModuleStatus.LOCKED,
                topics=[f"Topic {i+1}" for i in range(3)],
                estimated_hours=4 + idx * 2,
                mastery_score=0.0,
            )
        )

    plan = LearningPlan(
        skill=target_skill,
        level=starting_level,
        modules=modules,
        created=datetime.now(),
    )

    return plan


with st.sidebar:
    st.header("Learning Setup")

    target_skill = st.text_input(
        "Target Skill",
        placeholder="e.g., Machine Learning",
        disabled=st.session_state.learning_plan is not None,
    )

    starting_level = st.selectbox(
        "Starting Level",
        ["beginner", "intermediate", "expert"],
        disabled=st.session_state.learning_plan is not None,
    )

    if st.button(
        "Generate Learning Plan",
        disabled=not target_skill or st.session_state.learning_plan is not None,
    ):
        with st.spinner("Generating personalized learning path..."):
            st.session_state.learning_plan = generate_learning_plan(
                target_skill, starting_level
            )

            st.session_state.agent = initialize_agent(target_skill, starting_level)

            welcome_msg = f"""Welcome! I've created a personalized learning path for **{target_skill}**.

            Your learning journey includes {len(st.session_state.learning_plan.modules)} modules designed for your {starting_level} level.

            **Module 1**: {st.session_state.learning_plan.modules[0].title}

            Type 'start quiz' to begin your first assessment, or ask me anything!"""

            st.session_state.messages.append(
                {"role": "assistant", "content": welcome_msg}
            )
            st.rerun()

    if st.session_state.learning_plan:
        st.divider()
        st.subheader("Learning Progress")

        plan = st.session_state.learning_plan

        for idx, module in enumerate(plan.modules):
            status_emoji = {
                ModuleStatus.COMPLETED: "completed",
                ModuleStatus.ACTIVE: "active",
                ModuleStatus.LOCKED: "locked",
            }

            with st.container():
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"{status_emoji[module.status]} **{module.title}**")
                with col2:
                    if module.mastery_score > 0:
                        st.markdown(f"*{module.mastery_score:.0f}%*")

                if module.status == ModuleStatus.ACTIVE:
                    st.progress(0.5, text="In Progress")
                elif module.status == ModuleStatus.COMPLETED:
                    st.progress(1.0, text="Complete")

col1, col2 = st.columns([2, 1])

with col1:
    st.header("Interactive Learning Console")

    chat_container = st.container(height=400)
    with chat_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    if prompt := st.chat_input(
        "Type your message...", disabled=not st.session_state.learning_plan
    ):
        st.session_state.messages.append({"role": "user", "content": prompt})

        with chat_container:
            with st.chat_message("user"):
                st.markdown(prompt)

        with st.spinner("Agent thinking..."):
            try:
                current_module = st.session_state.learning_plan.modules[
                    st.session_state.current_module_idx
                ]

                messages = []
                for msg in st.session_state.messages:
                    messages.append({"role": msg["role"], "content": msg["content"]})

                response = st.session_state.agent.invoke(
                    {"messages": messages},
                    config={"callbacks": [st.session_state.callback_handler]},
                )

                agent_message = response["messages"][-1].content

            except Exception as e:
                agent_message = f"I encountered an error: {str(e)}. Please try rephrasing your question."

        st.session_state.messages.append(
            {"role": "assistant", "content": agent_message}
        )

        with chat_container:
            with st.chat_message("assistant"):
                st.markdown(agent_message)

        st.rerun()

with col2:
    st.header("Agent Traceability")

    with st.expander("View Agent Reasoning Process", expanded=True):
        if st.session_state.callback_handler.trace_log:
            for trace in st.session_state.callback_handler.trace_log[-10:]:
                st.markdown(f"**{trace['timestamp']}**")

                st.markdown(f"**Tool**: `{trace.get('tool', 'N/A')}`")

                if "input" in trace:
                    st.markdown("**Input**")
                    st.text(trace["input"][:150])

                if "output" in trace:
                    st.markdown("**Output**")
                    st.text(trace["output"])

                st.divider()
        else:
            st.info("Agent tool calls will appear here as you interact...")

st.divider()
st.markdown(
    """
**LangChain Tool-Calling Agents, Custom Tools, Structured Outputs, and Adaptive Learning Logic
"""
)
