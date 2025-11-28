"""
Agent node functions for the ALIS LangGraph workflow.
Each function represents a specific agent action in the learning pipeline.
"""
import json
import time
import re
from typing import Dict, Any
from bson.objectid import ObjectId # Import ObjectId for MongoDB _id handling

from backend.models.state import ALISState, Goal, UserProfile, ConceptDict
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
    db = get_db_service() # Get MongoDB service instance

    user_id = state['user_id']
    
    user_prompt = (
        f"Erstelle einen SMART-Lernziel-Vertrag und den initialen Lernpfad "
        f"für folgendes Ziel: '{state['user_input']}'. "
        f"Antworte IMMER im JSON-Format mit den Schlüsseln 'goal_contract' und 'path_structure'."
    )
    
    llm_result = llm.call(ARCHITEKT_PROMPT, user_prompt, use_grounding=True)
    
    # Update state with LLM output
    state['llm_output'] = llm_result
    
    new_goal: Optional[Goal] = None
    new_path_structure: List[ConceptDict] = []
    
    if llm.use_simulation:
        # Simulation logic
        goal_id = str(ObjectId()) # Generate a new ObjectId for the simulated goal
        new_goal = Goal(
            goalId=goal_id,
            name=state['user_input'],
            fachgebiet="Simuliert",
            targetDate="2025-12-31",
            bloomLevel=3,
            messMetrik="Erfolgreich simulierte Lernschritte",
            status="In Arbeit"
        )
        new_path_structure = [
            ConceptDict(
                id="K1-Grundlagen",
                name="Basiswissen (Übersprungen)",
                status="Übersprungen",
                expertiseSource="P3 Experte",
                requiredBloomLevel=2
            ),
            ConceptDict(
                id="K2-Kernkonzept",
                name="Kernkonzepte",
                status="Offen",
                requiredBloomLevel=3
            ),
        ]
        state['current_concept'] = new_path_structure[1]
        state['goal_id'] = goal_id
        state['goal'] = new_goal
        state['path_structure'] = new_path_structure
    else:
        # Parse JSON output from LLM for real API calls
        try:
            # Architekt is instructed to respond in JSON format
            parsed_result = json.loads(llm_result)
            
            goal_contract = parsed_result.get('goal_contract', {})
            path_structure_data = parsed_result.get('path_structure', [])
            
            goal_id = str(ObjectId()) # Generate a new ObjectId for the goal
            new_goal = Goal(
                goalId=goal_id,
                name=goal_contract.get('name', state['user_input']),
                fachgebiet=goal_contract.get('fachgebiet', "Unbekannt"),
                targetDate=goal_contract.get('targetDate', "N/A"),
                bloomLevel=goal_contract.get('bloomLevel', 1),
                messMetrik=goal_contract.get('messMetrik', "N/A"),
                status=goal_contract.get('status', "In Arbeit")
            )
            
            new_path_structure = [ConceptDict(**c) for c in path_structure_data]
            
            state['goal_id'] = goal_id
            state['goal'] = new_goal
            state['path_structure'] = new_path_structure
            
            # Find the first open concept or default to the first in the path
            state['current_concept'] = next(
                (c for c in new_path_structure if c.get('status') == 'Offen'),
                new_path_structure[0] if new_path_structure else None
            )
                 
        except Exception as e:
            print(f"Error parsing LLM output in create_goal_path: {e}")
            # Fallback to a safe default to prevent crash
            goal_id = str(ObjectId())
            new_goal = Goal(
                goalId=goal_id,
                name=state['user_input'],
                fachgebiet="Fallback",
                targetDate="N/A",
                bloomLevel=1,
                messMetrik="N/A",
                status="In Arbeit"
            )
            new_path_structure = [ConceptDict(
                id="K1-Fallback",
                name=state['user_input'],
                status="Offen",
                requiredBloomLevel=1
            )]
            state['goal_id'] = goal_id
            state['goal'] = new_goal
            state['path_structure'] = new_path_structure
            state['current_concept'] = new_path_structure[0]

    # Save UserProfile if it's new or updated (assuming user_id already exists in state)
    # For now, we only update it, future will fetch and then update
    user_profile = state.get('user_profile', UserProfile())
    db.save_user_profile(user_id, user_profile)
    
    # Save the new Goal including its path_structure
    if new_goal:
        # Add path_structure directly to the goal document for simplicity in MongoDB
        new_goal['path_structure'] = new_path_structure
        db.save_goal(state['goal_id'], new_goal)
    
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
    
    # Update concept status in database using the new db_service method
    if state.get('goal_id') and state.get('current_concept'):
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
    db = get_db_service() # Get MongoDB service instance
    
    missing_concept_name = state['user_input']
    
    # Architekt now expects JSON output for path surgery
    user_prompt = (
        f"Führe die Pfad-Chirurgie durch. Die fehlende Grundlage ist: '{missing_concept_name}'. "
        f"Der aktuelle Pfad lautet: {json.dumps(state['path_structure'], ensure_ascii=False)}. "
        f"Antworte IMMER im JSON-Format mit dem Schlüssel 'path_structure' und 'new_current_concept'."
    )
    
    llm_result = llm.call(ARCHITEKT_PROMPT, user_prompt)
    
    new_path = state['path_structure'] # Default to current path
    new_current_concept = state['current_concept'] # Default to current concept

    if llm.use_simulation:
        # Create new concept for the identified gap (simulated)
        new_concept_sim = ConceptDict(
            id=f"N-{int(time.time())}",
            name=missing_concept_name,
            status="Offen",
            expertiseSource="P5.5 Remediation",
            requiredBloomLevel=1
        )
        new_path = [new_concept_sim] + state['path_structure']
        # Reactivate any previously skipped related concepts (simulated)
        for concept in new_path:
            if concept.get('id') == 'K1-Grundlagen': # Specific to simulation
                concept['status'] = 'Reaktiviert'
        new_current_concept = new_concept_sim
        state['llm_output'] = (
            f"Der Architekt (simuliert) hat das neue Kapitel **'{new_concept_sim['name']}'** eingefügt. "
            f"Wir machen sofort dort weiter!"
        )
    else:
        # Parse JSON output from LLM for real API calls
        try:
            parsed_result = json.loads(llm_result)
            new_path_data = parsed_result.get('path_structure', state['path_structure'])
            new_current_concept_data = parsed_result.get('new_current_concept', state['current_concept'])

            new_path = [ConceptDict(**c) for c in new_path_data]
            new_current_concept = ConceptDict(**new_current_concept_data)
            state['llm_output'] = llm_result # LLM output might contain human-readable message alongside JSON

        except Exception as e:
            print(f"Error parsing LLM output in perform_remediation: {e}")
            state['llm_output'] = f"Fehler bei der Pfad-Chirurgie. Bitte versuchen Sie es erneut. Details: {e}"

    state['path_structure'] = new_path
    state['current_concept'] = new_current_concept
    state['remediation_needed'] = False
    
    # Update the goal's path_structure in the database
    if state.get('goal_id') and state.get('goal'):
        # Assuming path_structure is stored within the goal document
        state['goal']['path_structure'] = new_path # Update the goal object in state
        db.save_goal(state['goal_id'], state['goal']) # Save the entire updated goal document

    # Log remediation action
    logging_service.create_log_entry(
        eventType="P5.5_Remediation",
        conceptId=new_current_concept['id'],
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
        f"Reagiere affektiv und hilfsbereit. Identifiziere auch die Emotion des Nutzers (Frustration, Verwirrung, Freude, Neutral)."
    )
    
    llm_result = llm.call(TUTOR_PROMPT, user_prompt)
    state['llm_output'] = llm_result
    
    # Log LLM's chat output
    # Attempt to extract emotionFeedback from LLM result if possible
    emotion_feedback_match = re.search(r"Emotion:\s*(Frustration|Verwirrung|Freude|Neutral)", llm_result)
    emotion_feedback = emotion_feedback_match.group(1) if emotion_feedback_match else "Neutral"
    
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
    db = get_db_service() # Get MongoDB service instance
    
    concept_name = state['current_concept']['name']
    required_level = state['current_concept'].get('requiredBloomLevel', 3)
    user_profile = state.get('user_profile', {})
    
    user_prompt = (
        f"Generiere 3 Testfragen für das Konzept '{concept_name}' "
        f"auf Bloom-Stufe {required_level}. "
        f"Nutzerprofil: {json.dumps(user_profile, ensure_ascii=False)}. "
        f"Antworte IMMER im JSON-Format mit dem Schlüssel 'test_questions'."
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


def evaluate_test(state: ALISState) -> ALISState:
    """
    P6: Kurator evaluates user's test answers.
    
    Args:
        state: Current ALIS state with original test questions in llm_output
               and user answers in user_input.
        
    Returns:
        Updated state with test evaluation results and next steps.
    """
    llm = get_llm_service()
    db = get_db_service()
    
    user_id = state['user_id']
    goal_id = state['goal_id']
    current_concept = state['current_concept']
    user_profile = state.get('user_profile', {})
    
    # Parse original test questions from llm_output
    try:
        original_test_questions_raw = json.loads(state['llm_output'])
        original_test_questions = original_test_questions_raw.get('test_questions', [])
    except Exception as e:
        print(f"Error parsing original test questions from llm_output: {e}")
        original_test_questions = []

    # Parse user answers from user_input
    try:
        user_answers = json.loads(state['user_input'])
    except Exception as e:
        print(f"Error parsing user answers from user_input: {e}")
        user_answers = {}

    if not original_test_questions:
        state['llm_output'] = "Fehler: Originale Testfragen konnten nicht geladen werden zur Bewertung."
        state['test_evaluation_result'] = {"passed": False, "score": 0, "feedback": "Fehler bei der Testbewertung.", "recommendation": "Wiederhole das Konzept."}
        return state

    evaluation_prompt = (
        f"Bewerte die Antworten des Nutzers auf die folgenden Testfragen für das Konzept '{current_concept.get('name')}'. "
        f"Originale Fragen (Kurator generiert): {json.dumps(original_test_questions, ensure_ascii=False)}\n\n"
        f"Nutzerantworten: {json.dumps(user_answers, ensure_ascii=False)}\n\n"
        f"Basierend auf den Bloom-Anforderungen des Konzepts ({current_concept.get('requiredBloomLevel', 3)}) und dem Nutzerprofil ({json.dumps(user_profile, ensure_ascii=False)}):\n"
        f"1. Gib eine Punktzahl (0-100) basierend auf der Korrektheit und Tiefe der Antworten. "
        f"2. Entscheide, ob der Nutzer den Test bestanden hat (passed: true/false). Bestehen bei >70%."
        f"3. Gib kurzes Feedback zur Leistung des Nutzers."
        f"4. Gib eine Empfehlung für den nächsten Schritt (z.B. 'Nächstes Konzept', 'Wiederholung', 'Remediation bei Lücke')."
        f"5. Gib für JEDE Frage eine detaillierte Auswertung im Array 'question_results' mit: id, question_text, user_answer, correct_answer, is_correct (boolean), explanation."
        f"Antworte IMMER im JSON-Format mit den Schlüsseln 'score', 'passed', 'feedback', 'recommendation', 'question_results'."
    )
    
    llm_evaluation_result = llm.call(KURATOR_PROMPT, evaluation_prompt)
    
    # Parse LLM's evaluation result
    try:
        evaluation_data = json.loads(llm_evaluation_result)
        score = evaluation_data.get('score', 0)
        passed = evaluation_data.get('passed', False)
        feedback = evaluation_data.get('feedback', "Kein spezifisches Feedback vom LLM.")
        recommendation = evaluation_data.get('recommendation', "N/A")
        question_results = evaluation_data.get('question_results', [])
    except Exception as e:
        print(f"Error parsing LLM evaluation result: {e}")
        score = 0
        passed = False
        feedback = "Fehler bei der Bewertung durch das LLM."
        recommendation = "Wiederhole das Konzept."
        question_results = []

    # Update current concept status in the database
    if goal_id and current_concept:
        new_concept_status = "Beherrscht" if passed else "Wiederholen"
        db.update_concept_status(
            goal_id,
            current_concept['id'],
            new_concept_status
        )
        current_concept['status'] = new_concept_status # Update state for next step

        # Also update status in path_structure if present
        if 'path_structure' in state and state['path_structure']:
            for concept in state['path_structure']:
                if concept.get('id') == current_concept['id']:
                    concept['status'] = new_concept_status
                    break

    # Update UserProfile with testScore (P7 logic)
    # For a full P7, we'd fetch the user profile, update it, and save it back.
    # For now, we update the state's user_profile and save it implicitly (if create_goal_path is called again).
    # A dedicated user profile update function in db_service would be better.
    user_profile['lastTestScore'] = score
    
    # Log the test evaluation
    logging_service.create_log_entry(
        eventType="P6_Test_Evaluation",
        conceptId=current_concept['id'],
        textContent=f"Testfragen: {json.dumps(original_test_questions)}, Antworten: {json.dumps(user_answers)}",
        testScore=score,
        kognitiveDiskrepanz="Hoch" if not passed else "Niedrig", # Simplified
        emotionFeedback="Neutral" # Could be derived from answers/evaluation
    )

    state['llm_output'] = feedback # Human-readable feedback for the UI
    state['test_evaluation_result'] = {
        "passed": passed, 
        "score": score, 
        "feedback": feedback, 
        "recommendation": recommendation,
        "question_results": question_results
    }
    
    # This state key will be used by the workflow to decide next steps (P7 logic)
    state['test_passed'] = passed 

    return state
