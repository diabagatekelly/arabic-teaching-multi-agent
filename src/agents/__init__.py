"""Multi-agent system for Arabic language teaching."""

from .content_agent import ContentAgent
from .grading_agent import GradingAgent
from .teaching_agent import TeachingAgent

__all__ = ["TeachingAgent", "GradingAgent", "ContentAgent"]
