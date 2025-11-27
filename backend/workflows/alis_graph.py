"""
LangGraph workflow definition for ALIS.
Orchestrates the flow between different agent nodes.
"""
from langgraph.graph import StateGraph, END

from backend.models.state import ALISState
from backend.agents.nodes import (
    create_goal_path,
    generate_material,
    start_remediation_diagnosis,
    perform_remediation,
    process_chat,
    generate_test
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


def build_alis_graph():
    """
    Builds the LangGraph state machine for ALIS.
    
    The workflow follows this structure:
    1. P1/P3: Goal setting and path creation (Architekt)
    2. P4: Material generation (Kurator)
    3. P5: Learning phase with chat (Tutor)
    4. P5.5: Optional remediation loop (Tutor → Architekt → back to P4)
    5. P6: Test generation (Kurator)
    
    Returns:
        Compiled LangGraph workflow
    """
    workflow = StateGraph(ALISState)
    
    # Add nodes (agents/phases)
    workflow.add_node("P1_P3_Goal_Path_Creation", create_goal_path)
    workflow.add_node("P4_Material_Generation", generate_material)
    workflow.add_node("P5_Chat_Tutor", process_chat)
    workflow.add_node("P5_5_Diagnosis", start_remediation_diagnosis)
    workflow.add_node("P5_5_Remediation_Execution", perform_remediation)
    workflow.add_node("P6_Test_Generation", generate_test)
    
    # Set entry point
    workflow.set_entry_point("P1_P3_Goal_Path_Creation")
    
    # Add edges (transitions)
    
    # P1/P3 Flow: Goal creation → Material generation
    workflow.add_edge("P1_P3_Goal_Path_Creation", "P4_Material_Generation")
    
    # P4 Flow: Material → Chat/Learning
    workflow.add_edge("P4_Material_Generation", "P5_Chat_Tutor")
    
    # P5 Flow: Chat can lead to remediation or test
    workflow.add_conditional_edges(
        "P5_Chat_Tutor",
        should_remediate,
        {
            "remediate": "P5_5_Diagnosis",      # Gap reported
            "continue": "P6_Test_Generation"    # Standard flow to test
        }
    )
    
    # P5.5 Flow: Remediation loop
    # After diagnosis, architect must modify the path
    workflow.add_edge("P5_5_Diagnosis", "P5_5_Remediation_Execution")
    
    # After path correction, immediately generate material for new concept (N1)
    workflow.add_edge("P5_5_Remediation_Execution", "P4_Material_Generation")
    
    # P6 Flow: Test ends the cycle for this concept
    workflow.add_edge("P6_Test_Generation", END)
    
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
