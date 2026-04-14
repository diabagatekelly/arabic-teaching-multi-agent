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

from langgraph.graph import END, START, StateGraph

from src.agents import ContentAgent, GradingAgent, TeachingAgent

from .nodes import ContentNode, GradingNode, TeachingNode
from .state import SystemState

logger = logging.getLogger(__name__)


def create_teaching_graph(
    teaching_agent: TeachingAgent,
    grading_agent: GradingAgent,
    content_agent: ContentAgent,
) -> StateGraph:
    """
    Create the LangGraph orchestrator for multi-agent teaching.

    Args:
        teaching_agent: Agent 1 (Teaching/Feedback)
        grading_agent: Agent 2 (Answer validation)
        content_agent: Agent 3 (Exercise generation)

    Returns:
        Compiled LangGraph StateGraph
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
) -> dict[str, callable]:
    """Create node wrappers for each agent."""
    return {
        "teaching": TeachingNode(teaching_agent),
        "grading": GradingNode(grading_agent),
        "content": ContentNode(content_agent),
    }


def _build_graph(nodes: dict[str, callable]) -> StateGraph:
    """Construct the state graph with nodes and edges."""
    graph = StateGraph(SystemState)

    for name, node in nodes.items():
        graph.add_node(name, node)

    graph.add_edge(START, "teaching")

    graph.add_conditional_edges(
        "teaching",
        _route_from_teaching,
        {
            "content": "content",  # Teaching needs exercise
            "user": END,  # Wait for user (conversation paused)
            "end": END,  # Session complete
        },
    )

    graph.add_conditional_edges(
        "content",
        _route_from_content,
        {
            "user": END,  # Wait for user to answer exercise
            "teaching": "teaching",  # Error fallback
        },
    )

    graph.add_edge("grading", "teaching")  # Always return to teaching for feedback

    return graph


def _route_from_teaching(state: SystemState) -> str:
    """
    Route after teaching node execution.

    Possible routes:
    - "content" if teaching agent needs exercise
    - "user" if waiting for user input
    - "end" if session complete
    """
    if state.next_agent == "agent3":
        return "content"
    elif state.next_agent == "user":
        return "user"
    elif state.next_agent == "end":
        return "end"
    else:
        # Default: wait for user
        return "user"


def _route_from_content(state: SystemState) -> str:
    """
    Route after content node execution.

    Possible routes:
    - "user" if exercise generated (wait for user answer)
    - "teaching" if error occurred (fallback)
    """
    if state.next_agent == "user":
        return "user"
    else:
        # Error fallback: return to teaching
        return "teaching"


def run_conversation_turn(
    graph: StateGraph, state: SystemState, user_input: str | None = None
) -> SystemState:
    """
    Execute one turn of conversation through the graph.

    Args:
        graph: Compiled LangGraph
        state: Current system state
        user_input: Optional user message

    Returns:
        Updated system state after processing
    """
    try:
        if user_input:
            state = _handle_user_input(state, user_input)

        result_dict = graph.invoke(state)

        if isinstance(result_dict, dict):
            return SystemState.from_dict(result_dict)
        return result_dict

    except Exception as e:
        logger.error(f"Error in conversation turn: {e}")
        state.add_message("system", f"Error: {str(e)}")
        return state


def _handle_user_input(state: SystemState, user_input: str) -> SystemState:
    """Add user input and determine next agent based on context."""
    state.add_message("user", user_input)

    if state.pending_exercise and state.awaiting_user_answer:
        state.next_agent = "agent2"  # User answering exercise → grade it
    else:
        state.next_agent = "agent1"  # User talking to teaching agent

    return state


def create_new_session(user_id: str, session_id: str) -> SystemState:
    """
    Create a new teaching session.

    Args:
        user_id: Unique user identifier
        session_id: Unique session identifier

    Returns:
        Initialized SystemState
    """
    state = SystemState(user_id=user_id, session_id=session_id)

    logger.info(f"Created new session: {session_id} for user: {user_id}")
    return state


# Example usage (for testing/development)
def main():
    """Example usage of the orchestration layer."""
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
    main()
