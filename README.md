# Adaptive Learning Agent

LLM powered personalized learning assistant built with LangChain agents and Streamlit.

## Features

- Personalized learning path generation
- Interactive quiz generation with structured outputs
- Progress tracking and knowledge profiling
- Real-time resource search
- Tool-calling agent with traceability

## Tech Stack

- LangChain 1.0 (tool-calling agents)
- OpenAI GPT-4o
- Streamlit
- Pydantic (structured outputs)
- Python 3.12+

## Setup

1. Install dependencies with uv:

```bash
uv sync
```

2. Create `.env` file:

```bash
cp .env.example .env
```

3. Add your OpenAI API key to `.env`:

```
OPENAI_API_KEY=your_key_here
```

## Usage

### Run the web application:

```bash
streamlit run app.py
```

### Run component demos:

```bash
python demo.py
```

## Custom Tools

### KnowledgeProfileManager

Manages persistent user learning profiles and progress tracking.

### StructuredQuizGenerator

Generates validated quizzes using Pydantic output parsers.

### RealTimeResourceSearch

Searches for educational resources using web search APIs.

## Architecture

Built using LangChain's `create_agent` with tool calling architecture for efficient multi-tool coordination. The agent uses implicit reasoning with explicit tool call tracking for traceability.
