"""
ADK Agent scaffold integrating StudyConcierge tools.
"""
from typing import Optional, Callable, Any
import logging

logger = logging.getLogger(__name__)

try:
    from google.adk.agents import Agent as AdkAgent
except Exception:
    AdkAgent = None

# Optional: wrap project tools as callable functions ADK can use

def make_search_tool(search_tool) -> Callable[[str, int], Any]:
    async def search_web(query: str, num_results: int = 5) -> Any:
        return await search_tool.search(query, num_results)
    return search_web


def make_pdf_extract_tool(pdf_tool) -> Callable[[str], Any]:
    async def extract_pdf_text(path: str) -> Any:
        return await pdf_tool.extract_text(path)
    return extract_pdf_text


def build_summarizer_adk_agent(memory_bank=None, search_tool=None, pdf_tool=None, model: Optional[str] = None):
    """
    Build an ADK Agent that can summarize content using project tools.
    Returns None if ADK is not available.
    """
    if AdkAgent is None:
        logger.warning("google-adk not available; returning None from build_summarizer_adk_agent")
        return None

    instruction = (
        "You are a helpful academic assistant. You can search the web and read PDFs. "
        "When the user asks to summarize, produce a concise summary and key points."
    )

    tools = []
    if search_tool is not None:
        tools.append(make_search_tool(search_tool))
    if pdf_tool is not None:
        tools.append(make_pdf_extract_tool(pdf_tool))

    agent = AdkAgent(
        name="study_summarizer",
        model=model or "gemini-2.5-flash",
        instruction=instruction,
        description="Summarizer agent powered by ADK with project tools",
        tools=tools if tools else None,
    )

    return agent


def build_planner_adk_agent(memory_bank=None, model: Optional[str] = None):
    """Build an ADK Agent for creating study plans."""
    if AdkAgent is None:
        logger.warning("google-adk not available; returning None from build_planner_adk_agent")
        return None
    instruction = (
        "You create detailed study plans from syllabus, deadlines, and preferences. "
        "Return strict JSON with keys: created_at, syllabus, deadlines, preferences, daily_schedule, weekly_goals."
    )
    agent = AdkAgent(
        name="study_planner",
        model=model or "gemini-2.5-flash",
        instruction=instruction,
        description="Planner agent powered by ADK",
    )
    return agent


def build_quiz_adk_agent(memory_bank=None, model: Optional[str] = None):
    """Build an ADK Agent for generating quizzes."""
    if AdkAgent is None:
        logger.warning("google-adk not available; returning None from build_quiz_adk_agent")
        return None
    instruction = (
        "Generate multiple-choice quizzes from a topic and content. "
        "Return strict JSON with keys: topic, generated_at, questions (with question, options, correct_answer, explanation)."
    )
    agent = AdkAgent(
        name="study_quiz",
        model=model or "gemini-2.5-flash",
        instruction=instruction,
        description="Quiz agent powered by ADK",
    )
    return agent


def build_session_adk_agent(memory_bank=None, model: Optional[str] = None):
    """Build an ADK Agent for summarizing session data."""
    if AdkAgent is None:
        logger.warning("google-adk not available; returning None from build_session_adk_agent")
        return None
    instruction = (
        "Summarize session progress and suggest next steps in a concise paragraph."
    )
    agent = AdkAgent(
        name="session_summarizer",
        model=model or "gemini-2.5-flash",
        instruction=instruction,
        description="Session summary agent powered by ADK",
    )
    return agent