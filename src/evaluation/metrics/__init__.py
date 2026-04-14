"""Evaluation metrics for Arabic Teaching Multi-Agent System.

Metrics are organized by agent:
- Shared: JSONValidityMetric, StructureMetric, extract_json (used by multiple agents)
- Agent 1 (Teaching): SentimentMetric, FeedbackAppropriatenessMetric, HasNavigationMetric, StructureValidMetric
- Agent 2 (Grading): AccuracyMetric
- Agent 3 (Content): ExerciseQualityMetric
"""

# Shared metrics and utilities
# Agent 3 (Content Agent) metrics
from .content_agent_metrics import ExerciseQualityMetric

# Agent 2 (Grading Agent) metrics
from .grading_agent_metrics import AccuracyMetric
from .shared_metrics import JSONValidityMetric, StructureMetric, extract_json

# Agent 1 (Teaching Agent) metrics
from .teaching_agent_metrics import (
    FeedbackAppropriatenessMetric,
    HasNavigationMetric,
    SentimentMetric,
    StructureValidMetric,
)

__all__ = [
    # Shared
    "extract_json",
    "JSONValidityMetric",
    "StructureMetric",
    # Agent 1
    "SentimentMetric",
    "FeedbackAppropriatenessMetric",
    "HasNavigationMetric",
    "StructureValidMetric",
    # Agent 2
    "AccuracyMetric",
    # Agent 3
    "ExerciseQualityMetric",
]
