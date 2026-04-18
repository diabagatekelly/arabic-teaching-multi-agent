"""LangGraph orchestrator for multi-agent teaching system.

This module defines the state machine that coordinates Agent 1 (Teaching),
Agent 2 (Grading), and Agent 3 (Content) to deliver Arabic language lessons.

Flow:
1. User starts session → Teaching Agent introduces lesson
2. Teaching Agent requests exercise → Content Agent generates it
3. User answers exercise → Grading Agent validates answer
4. Grading complete → Teaching Agent provides feedback
5. Repeat until lesson complete

State: Stored in SystemState (see state.py)
Nodes: TeachingNode, GradingNode, ContentNode (see nodes.py)
Routing: Conditional edges based on conversation state (see routing.py)
"""

import logging
from collections.abc import Callable

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from src.agents import ContentAgent, GradingAgent, TeachingAgent

from .nodes import ContentNode, GradingNode, TeachingNode
from .routing import get_next_agent_from_user_input, route_next_node
from .state import SystemState

logger = logging.getLogger(__name__)


def create_teaching_graph(
    teaching_agent: TeachingAgent,
    grading_agent: GradingAgent,
    content_agent: ContentAgent,
) -> CompiledStateGraph:
    """
    Create the LangGraph orchestrator for multi-agent teaching.

    Args:
        teaching_agent: Agent 1 (Teaching/Feedback)
        grading_agent: Agent 2 (Answer validation)
        content_agent: Agent 3 (Exercise generation)

    Returns:
        Compiled LangGraph graph (usable with `.invoke`)
    """
    nodes = _create_nodes(teaching_agent, grading_agent, content_agent)
    graph = _build_graph(nodes)
    compiled_graph = graph.compile()

    logger.info("✓ Teaching graph compiled successfully")
    return compiled_graph


def _create_nodes(
    teaching_agent: TeachingAgent,
    grading_agent: GradingAgent,
    content_agent: ContentAgent,
) -> dict[str, Callable]:
    """Create node wrappers for each agent."""
    return {
        "teaching": TeachingNode(teaching_agent, content_agent=content_agent),
        "grading": GradingNode(grading_agent),
        "content": ContentNode(content_agent),
    }


def _build_graph(nodes: dict[str, Callable]) -> StateGraph:
    """Construct the state graph with nodes and edges."""
    graph = StateGraph(SystemState)

    for name, node in nodes.items():
        graph.add_node(name, node)

    # All routing uses centralized route_next_node function
    graph.add_conditional_edges(
        START,
        route_next_node,
        {
            "teaching": "teaching",
            "grading": "grading",
            "content": "content",
            "user": END,
            "end": END,
        },
    )

    graph.add_conditional_edges(
        "teaching",
        route_next_node,
        {
            "content": "content",
            "user": END,
            "end": END,
        },
    )

    graph.add_conditional_edges(
        "content",
        route_next_node,
        {
            "user": END,
            "teaching": "teaching",
        },
    )

    graph.add_edge("grading", "teaching")  # Always return to teaching for feedback

    return graph


def run_conversation_turn(
    graph: CompiledStateGraph, state: SystemState, user_input: str | None = None
) -> SystemState:
    """
    Execute one turn of conversation through the graph.

    Args:
        graph: Compiled LangGraph graph
        state: Current system state
        user_input: Optional user message

    Returns:
        Updated system state after processing
    """
    try:
        if user_input:
            state.add_message("user", user_input)
            state.next_agent = get_next_agent_from_user_input(user_input, state)

        result_dict = graph.invoke(state)

        if isinstance(result_dict, dict):
            return SystemState.from_dict(result_dict)
        return result_dict

    except Exception as e:
        logger.error(f"Error in conversation turn: {e}")
        state.add_message("system", f"Error: {str(e)}")
        return state


def create_new_session(user_id: str, session_id: str, lesson_number: int = 1) -> SystemState:
    """
    Create a new teaching session.

    Args:
        user_id: Unique user identifier
        session_id: Unique session identifier
        lesson_number: Lesson to start with (default: 1)

    Returns:
        Initialized SystemState
    """
    state = SystemState(user_id=user_id, session_id=session_id, current_lesson=lesson_number)

    logger.info(f"Created new session: {session_id} for user: {user_id}, lesson: {lesson_number}")
    return state


def initialize_lesson_content(
    state: SystemState, content_node: ContentNode, grading_node: GradingNode
) -> SystemState:
    """
    Initialize lesson by caching content and pre-loading grading rules.

    Per ARCHITECTURE.md:
    1. Agent 3 caches ALL lesson content (vocabulary + grammar)
    2. Agent 2 pre-loads grammar rules for grading context

    This should be called once per lesson before teaching begins.

    Args:
        state: Current system state
        content_node: ContentNode for caching content
        grading_node: GradingNode for pre-loading rules

    Returns:
        Updated state with cached content and pre-loaded rules
    """
    logger.info(f"Initializing lesson {state.current_lesson} content")

    # Content node caches all lesson content
    state = content_node.initialize_lesson(state)

    # Grading node pre-loads grammar rules
    grading_node.preload_grammar_rules(state)

    logger.info(f"Lesson {state.current_lesson} initialization complete")
    return state


def _example_main():
    """
    Example usage of the orchestration layer.

    NOTE: This is a development example only and should not be imported.
    For production use, create a separate script that imports from this module.
    """
    from transformers import AutoModelForCausalLM, AutoTokenizer

    logger.info("Loading models...")
    model_3b = AutoModelForCausalLM.from_pretrained("Qwen/Qwen2.5-3B-Instruct", device_map="auto")
    tokenizer_3b = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-3B-Instruct")

    teaching_agent = TeachingAgent(model_3b, tokenizer_3b)
    grading_agent = GradingAgent(model_3b, tokenizer_3b)
    content_agent = ContentAgent(model_3b, tokenizer_3b)

    graph = create_teaching_graph(teaching_agent, grading_agent, content_agent)
    state = create_new_session(user_id="test_user", session_id="session_001")

    state = run_conversation_turn(graph, state)
    print("Agent:", state.conversation_history[-1].content)

    state = run_conversation_turn(graph, state, user_input="I'm ready to learn!")
    print("Agent:", state.conversation_history[-1].content)

    logger.info("✓ Example conversation completed")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    _example_main()
