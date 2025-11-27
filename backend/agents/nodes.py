"""
Agent node functions for the ALIS LangGraph workflow.
Each function represents a specific agent action in the learning pipeline.
"""
import json
import time
from typing import Dict, Any

from backend.models.state import ALISState
from backend.agents.prompts import ARCHITEKT_PROMPT, KURATOR_PROMPT, TUTOR_PROMPT
from backend.services.llm_service import get_llm_service
from backend.services.db_service import get_db_service
from backend.services.logging_service import logging_service


def create_goal_path(state: ALISState) -> ALISState:
    """
    P1/P3: Architekt creates SMART goal and initial learning path.
    
    Args:
        state: Current ALIS state with user input
        
    Returns:
        Updated state with goal, path structure, and current concept
    """
    llm = get_llm_service()
    
    user_prompt = (
        f"Erstelle einen SMART-Lernziel-Vertrag und den initialen Lernpfad "
        f"für folgendes Ziel: '{state['user_input']}'"
    )
    
    llm_result = llm.call(ARCHITEKT_PROMPT, user_prompt, use_grounding=True)
    
    # Update state with LLM output
    state['llm_output'] = llm_result
    
    # In simulation mode, create a sample path structure
    # In production, this would parse the LLM response
    if llm.use_simulation:
        state['path_structure'] = [
            {
                "id": "K1-Grundlagen",
                "name": "Basiswissen (Übersprungen)",
                "status": "Übersprungen",
                "expertiseSource": "P3 Experte",
                "requiredBloomLevel": 2
            },
            {
                "id": "K2-Kernkonzept",
                "name": "Kernkonzepte",
                "status": "Offen",
                "requiredBloomLevel": 3
            },
        ]
        state['current_concept'] = state['path_structure'][1]
    
    # Log the goal creation
    logging_service.create_log_entry(
        eventType="P1_Zielsetzung",
        conceptId=state['current_concept']['id'] if state.get('current_concept') else None,
        textContent=state['user_input'],
        groundingSources=None # Architekt output might have sources if grounding is active
    )
    
    return state


def generate_material(state: ALISState) -> ALISState:
    """
    P4: Kurator generates learning material for the current concept.
    
    Args:
        state: Current ALIS state with current concept
        
    Returns:
        Updated state with generated material
    """
    llm = get_llm_service()
    db = get_db_service()
    
    concept_name = state['current_concept']['name']
    user_profile = state.get('user_profile', {})
    
    user_prompt = (
        f"Generiere Lernmaterial für das Konzept: '{concept_name}'. "
        f"Nutze den folgenden Nutzerkontext: {json.dumps(user_profile, ensure_ascii=False)}"
    )
    
    llm_result = llm.call(KURATOR_PROMPT, user_prompt, use_grounding=True)
    state['llm_output'] = llm_result
    
    # Update concept status in database
    if state.get('goal_id'):
        db.update_concept_status(
            state['goal_id'],
            state['current_concept']['id'],
            'Aktiv'
        )
        
    # Log material generation
    logging_service.create_log_entry(
        eventType="P4_Material",
        conceptId=state['current_concept']['id'],
        textContent=state['llm_output'],
        groundingSources=None # Kurator output might have sources if grounding is active
    )
    
    return state


def start_remediation_diagnosis(state: ALISState) -> ALISState:
    """
    P5.5, Part 1: Tutor starts diagnosis when knowledge gap is detected.
    
    Args:
        state: Current ALIS state
        
    Returns:
        Updated state with diagnosis prompt and remediation flag
    """
    llm = get_llm_service()
    
    concept_name = state['current_concept']['name']
    user_prompt = (
        f"Der Nutzer hat bei dem Konzept '{concept_name}' den Lücken-Indikator ausgelöst. "
        f"Starte die Diagnose."
    )
    
    llm_result = llm.call(TUTOR_PROMPT, user_prompt)
    state['llm_output'] = llm_result
    state['remediation_needed'] = True
    
    # Log remediation diagnosis start
    logging_service.create_log_entry(
        eventType="P5.5_Lücken_Diagnose",
        conceptId=state['current_concept']['id'],
        textContent=state['llm_output'],
        emotionFeedback="Lücken-Indikator ausgelöst" # Placeholder
    )
    
    return state


def perform_remediation(state: ALISState) -> ALISState:
    """
    P5.5, Part 2: Architekt performs path surgery to insert missing concept.
    
    Args:
        state: Current ALIS state with user input identifying the gap
        
    Returns:
        Updated state with modified path structure
    """
    llm = get_llm_service()
    
    missing_concept_name = state['user_input']
    
    user_prompt = (
        f"Führe die Pfad-Chirurgie durch. Die fehlende Grundlage ist: '{missing_concept_name}'. "
        f"Der aktuelle Pfad lautet: {json.dumps(state['path_structure'], ensure_ascii=False)}"
    )
    
    llm_result = llm.call(ARCHITEKT_PROMPT, user_prompt)
    
    # Create new concept for the identified gap
    new_concept = {
        "id": f"N-{int(time.time())}",
        "name": missing_concept_name,
        "status": "Offen",
        "expertiseSource": "P5.5 Remediation",
        "requiredBloomLevel": 1
    }
    
    # Insert at the beginning of the path
    new_path = [new_concept] + state['path_structure']
    
    # Reactivate any previously skipped related concepts
    for concept in new_path:
        if concept.get('id') == 'K1-Grundlagen':
            concept['status'] = 'Reaktiviert'
    
    state['path_structure'] = new_path
    state['current_concept'] = new_concept
    state['remediation_needed'] = False
    state['llm_output'] = (
        f"Der Architekt hat das neue Kapitel **'{new_concept['name']}'** eingefügt. "
        f"Wir machen sofort dort weiter!"
    )
    
    # Log remediation action
    logging_service.create_log_entry(
        eventType="P5.5_Remediation",
        conceptId=new_concept['id'],
        textContent=state['llm_output']
    )
    
    return state


def process_chat(state: ALISState) -> ALISState:
    """
    P5/P7: Tutor responds to chat requests and provides adaptive feedback.
    
    Args:
        state: Current ALIS state with user input
        
    Returns:
        Updated state with tutor response
    """
    llm = get_llm_service()
    
    current_topic = state['current_concept'].get('name', 'aktuelles Thema')
    user_input = state['user_input']
    
    # Log user's chat input
    logging_service.create_log_entry(
        eventType="P5_Chat_User_Input",
        conceptId=state['current_concept']['id'],
        textContent=user_input
    )
    
    user_prompt = (
        f"Der Nutzer fragt: '{user_input}'. "
        f"Das aktuelle Thema ist: {current_topic}. "
        f"Reagiere affektiv und hilfsbereit."
    )
    
    llm_result = llm.call(TUTOR_PROMPT, user_prompt)
    state['llm_output'] = llm_result
    
    # Log LLM's chat output
    # For emotionFeedback, a more sophisticated NLP model would be needed to extract it
    # For now, we'll leave it as None or a placeholder if easily detectable.
    emotion_feedback = "Neutral" # Placeholder for now; could be parsed from llm_result
    
    logging_service.create_log_entry(
        eventType="P5_Chat_LLM_Output",
        conceptId=state['current_concept']['id'],
        textContent=llm_result,
        emotionFeedback=emotion_feedback
    )
    
    return state


def generate_test(state: ALISState) -> ALISState:
    """
    P6: Kurator generates comprehension test questions.
    
    Args:
        state: Current ALIS state with current concept
        
    Returns:
        Updated state with test questions
    """
    llm = get_llm_service()
    
    concept_name = state['current_concept']['name']
    required_level = state['current_concept'].get('requiredBloomLevel', 3)
    user_profile = state.get('user_profile', {})
    
    user_prompt = (
        f"Generiere 3 Testfragen für das Konzept '{concept_name}' "
        f"auf Bloom-Stufe {required_level}. "
        f"Nutzerprofil: {json.dumps(user_profile, ensure_ascii=False)}"
    )
    
    llm_result = llm.call(KURATOR_PROMPT, user_prompt)
    state['llm_output'] = llm_result
    
    # Log test generation
    logging_service.create_log_entry(
        eventType="P6_Test_Generation",
        conceptId=state['current_concept']['id'],
        textContent=state['llm_output']
    )
    
    return state
