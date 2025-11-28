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
    """
    import sys
    print(f"\n--- DEBUG: should_progress called ---", file=sys.stderr)
    print(f"  state.get('test_passed'): {state.get('test_passed')}", file=sys.stderr)
    
    if state.get('test_passed'):
        current_concept_id = state.get('current_concept', {}).get('id')
        path_structure = state.get('path_structure', [])
        
        print(f"  current_concept_id: {current_concept_id}", file=sys.stderr)
        print(f"  len(path_structure): {len(path_structure)}", file=sys.stderr)
        
        if current_concept_id:
            current_index = -1
            for i, concept in enumerate(path_structure):
                if concept.get('id') == current_concept_id:
                    current_index = i
                    break
            
            print(f"  current_index: {current_index}", file=sys.stderr)
            
            if current_index != -1 and current_index + 1 < len(path_structure):
                # There is a next concept
                # Set the next concept as current_concept in state for the next P4 call
                state['current_concept'] = path_structure[current_index + 1] # <<-- CRITICAL STATE UPDATE
                print(f"  Returning 'next_concept'. New current_concept: {state['current_concept']['name']}", file=sys.stderr)
                return "next_concept"
        
        # No more concepts or current concept not found
        print(f"  Returning 'goal_complete'.", file=sys.stderr)
        return "goal_complete"
    else:
        # Test not passed, re-study current concept
        print(f"  Returning 're_study'. Test not passed.", file=sys.stderr)
        return "re_study"


def build_alis_graph():
    """
    Builds the LangGraph state machine for ALIS.
    
    The workflow follows this structure:
    1. P1/P3: Goal setting and path creation (Architekt)
    2. P4: Material generation (Kurator)
    3. P5: Learning phase with chat (Tutor)
    4. P5.5: Optional remediation loop (Tutor → Architekt → back to P4)
    5. P6: Test generation (Kurator)
    6. P7: Test evaluation and progression (Kurator/Tutor logic)
    
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
    workflow.add_node("P7_Test_Evaluation", evaluate_test) # Add the new evaluation node
    
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
    
    # P6 Flow: Test generation → Test Evaluation
    workflow.add_edge("P6_Test_Generation", "P7_Test_Evaluation")
    
    # P7 Flow: Test Evaluation leads to progression, re-study, or end
    workflow.add_conditional_edges(
        "P7_Test_Evaluation",
        should_progress,
        {
            "next_concept": "P4_Material_Generation", # Test passed, move to next concept
            "goal_complete": END,                     # Test passed, no more concepts
            "re_study": "P4_Material_Generation"      # Test not passed, re-study current concept
        }
    )
    
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
