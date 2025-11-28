import math
from langgraph.graph import StateGraph, END

from backend.models.state import ALISState
from backend.agents.nodes import (
    create_goal_path,
    generate_material,
    start_remediation_diagnosis,
    perform_remediation,
    process_chat,
    generate_test,
    evaluate_test # Import the new evaluate_test node
)


def should_remediate(state: ALISState) -> str:
    """
    Decision point: Should the remediation loop be started?
    
    Args:
        state: Current ALIS state
        
    Returns:
        "remediate" if remediation is needed, "continue" otherwise
    """
    if state.get('remediation_needed'):
        return "remediate"
    return "continue"


def should_progress(state: ALISState) -> str:
    """
    Decision point after test evaluation: Should the learner progress to the next concept,
    re-study the current concept, or end the goal? (P7 logic)
    This function *reads* the state set by the P7_Test_Evaluation node and is robust
    against 'current_concept' being None.
    """
    import sys
    print(f"\n--- DEBUG: should_progress called ---", file=sys.stderr)
    print(f"  state.get('test_passed'): {state.get('test_passed')}", file=sys.stderr)
    
    if not state.get('test_passed'):
        # Test was not passed, so re-study the current concept.
        # The 'current_concept' in the state has not been advanced by the evaluate_test node.
        print(f"  Returning 're_study'.", file=sys.stderr)
        return "re_study"
    
    # Test was passed. Check if the evaluate_test node provided a next concept.
    if state.get('current_concept'):
        # The evaluate_test node has set the next concept to continue the journey.
        print(f"  Returning 'next_concept'.", file=sys.stderr)
        return "next_concept"
    else:
        # The evaluate_test node set current_concept to None, indicating the goal is complete.
        print(f"  Returning 'goal_complete'.", file=sys.stderr)
        return "goal_complete"


def route_workflow(state: ALISState) -> str:
    """
    Router function to determine the entry point based on state['next_step'].
    """
    next_step = state.get('next_step')
    if next_step in ["P1_P3_Goal_Path_Creation", "P4_Material_Generation", "P5_Chat_Tutor", "P5_5_Diagnosis"]:
        return next_step
    return "P1_P3_Goal_Path_Creation" # Default

def build_alis_graph():
    """
    Builds the LangGraph state machine for ALIS.
    """
    workflow = StateGraph(ALISState)
    
    # Add nodes (agents/phases)
    workflow.add_node("P1_P3_Goal_Path_Creation", create_goal_path)
    workflow.add_node("P4_Material_Generation", generate_material)
    workflow.add_node("P5_Chat_Tutor", process_chat)
    workflow.add_node("P5_5_Diagnosis", start_remediation_diagnosis)
    workflow.add_node("P5_5_Remediation_Execution", perform_remediation)
    
    # Add a dummy start node for routing
    def start_router(state):
        return state
    
    workflow.add_node("START_ROUTER", start_router)
    workflow.set_entry_point("START_ROUTER")
    
    # Add conditional edges from router to the correct start node
    workflow.add_conditional_edges(
        "START_ROUTER",
        route_workflow,
        {
            "P1_P3_Goal_Path_Creation": "P1_P3_Goal_Path_Creation",
            "P4_Material_Generation": "P4_Material_Generation",
            "P5_Chat_Tutor": "P5_Chat_Tutor",
            "P5_5_Diagnosis": "P5_5_Diagnosis"
        }
    )
    
    # Add edges (transitions)
    
    # P1/P3 Flow: After goal creation, the graph should end.
    workflow.add_edge("P1_P3_Goal_Path_Creation", END)
    
    # P4 Flow: Material → Chat/Learning
    # Note: If we start at P4, we want to go to P5 (Chat) afterwards? 
    # Actually, P4 generates material and returns. The frontend then calls P5 (Chat) separately if needed.
    # But in the original graph: workflow.add_edge("P4_Material_Generation", "P5_Chat_Tutor")
    # This implies that after generating material, we immediately enter chat mode?
    # If get_material calls P4, and P4 goes to P5, then P5 will run with empty user input?
    # Let's check process_chat. It uses state['user_input'].
    # If get_material payload has no user_input (or empty), P5 might fail or do something weird.
    # Let's keep the original edge for now, but be aware.
    workflow.add_edge("P4_Material_Generation", END) # Changed to END to stop after material generation
    
    # P5 Flow: Chat can lead to remediation
    workflow.add_conditional_edges(
        "P5_Chat_Tutor",
        should_remediate,
        {
            "remediate": "P5_5_Diagnosis",
            "continue": END  # Stop the graph here and wait for explicit user action
        }
    )
    
    # P5.5 Flow: Remediation loop
    # After diagnosis, architect must modify the path
    workflow.add_edge("P5_5_Diagnosis", "P5_5_Remediation_Execution")
    
    # After path correction, immediately generate material for new concept (N1)
    workflow.add_edge("P5_5_Remediation_Execution", "P4_Material_Generation")
    
    # P6/P7 (Test/Evaluation) flows are handled by direct API calls, not as part of this graph.
    
    return workflow.compile()


# Global workflow instance
_workflow_instance = None


def get_workflow():
    """
    Get or create the global workflow instance.
    
    Returns:
        Compiled LangGraph workflow
    """
    global _workflow_instance
    if _workflow_instance is None:
        _workflow_instance = build_alis_graph()
    return _workflow_instance
