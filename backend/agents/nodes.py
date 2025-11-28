"""
Agent node functions for the ALIS LangGraph workflow.
Each function represents a specific agent action in the learning pipeline.
"""
import json
import time
import re
from typing import Dict, Any, List, Optional
from bson.objectid import ObjectId

from backend.models.state import ALISState, Goal, UserProfile, ConceptDict
from backend.agents.prompts import ARCHITECT_PROMPT, CURATOR_PROMPT, TUTOR_PROMPT, ASSESSOR_PROMPT
from backend.services.llm_service import get_llm_service
from backend.services.db_service import get_db_service
from backend.services.logging_service import logging_service


def create_goal_path(state: ALISState) -> ALISState:
    """
    P1/P3: Architect creates SMART goal and initial learning path.
    """
    llm = get_llm_service()
    db = get_db_service()

    user_id = state['user_id']
    user_prompt = (
        f"[ACTION: CREATE_GOAL_PATH] "
        f"Create a SMART learning goal contract and the initial learning path "
        f"for the following goal: '{state['user_input']}'. "
        f"ALWAYS respond in JSON format with the keys 'goal_contract' and 'path_structure'."
    )
    llm_result = llm.call(ARCHITECT_PROMPT, user_prompt, use_grounding=True)
    
    state['llm_output'] = llm_result
    
    new_goal: Optional[Goal] = None
    new_path_structure: List[ConceptDict] = []
    
    try:
        parsed_result = json.loads(llm_result)
        
        goal_contract = parsed_result.get('goal_contract', {})
        path_structure_data = parsed_result.get('path_structure', [])
        
        goal_id = str(ObjectId())
        new_goal = Goal(
            goalId=goal_id,
            name=goal_contract.get('name', state['user_input']),
            fachgebiet=goal_contract.get('fachgebiet', "Unknown"),
            targetDate=goal_contract.get('targetDate', "N/A"),
            bloomLevel=goal_contract.get('bloomLevel', 1),
            messMetrik=goal_contract.get('successMetric', "N/A"),
            status="In Progress"
        )
        
        new_path_structure = [ConceptDict(**c) for c in path_structure_data]
        
        state['goal_id'] = goal_id
        state['goal'] = new_goal
        state['path_structure'] = new_path_structure
        
        state['current_concept'] = next(
            (c for c in new_path_structure if c.get('status') == 'Open'),
            new_path_structure[0] if new_path_structure else None
        )
             
    except Exception as e:
        print(f"Error parsing LLM output in create_goal_path: {e}")
        goal_id = str(ObjectId())
        new_goal = Goal(goalId=goal_id, name=state['user_input'], fachgebiet="Fallback", status="In Progress")
        new_path_structure = [ConceptDict(id="C1-Fallback", name=state['user_input'], status="Open", requiredBloomLevel=1)]
        state['goal_id'] = goal_id
        state['goal'] = new_goal
        state['path_structure'] = new_path_structure
        state['current_concept'] = new_path_structure[0]

    user_profile = state.get('user_profile', UserProfile())
    db.save_user_profile(user_id, user_profile)
    
    if new_goal:
        new_goal['path_structure'] = new_path_structure
        db.save_goal(state['goal_id'], new_goal)
    
    logging_service.create_log_entry(
        eventType="P1_Goal_Setting",
        conceptId=state['current_concept']['id'] if state.get('current_concept') else None,
        textContent=state['user_input']
    )
    
    return state


def generate_material(state: ALISState) -> ALISState:
    """
    P4: Curator generates learning material for the current concept.
    """
    llm = get_llm_service()
    db = get_db_service()
    
    concept_name = state['current_concept']['name']
    user_profile = state.get('user_profile', {})
    
    user_prompt = (
        f"[ACTION: GENERATE_MATERIAL] "
        f"Generate learning material for the concept: '{concept_name}'. "
        f"Use the following user context: {json.dumps(user_profile, ensure_ascii=False)}. "
    )
    
    # Add context from previous failed test if available (Remediation Loop)
    if state.get('test_evaluation_result') and not state['test_evaluation_result'].get('passed', True):
        feedback = state['test_evaluation_result'].get('feedback', '')
        user_prompt += f"The user previously failed a test on this concept. Feedback was: '{feedback}'. Please adapt the material to address these gaps."
    llm_result = llm.call(CURATOR_PROMPT, user_prompt, use_grounding=True)
    state['llm_output'] = llm_result
    
    if state.get('goal_id') and state.get('current_concept'):
        db.update_concept_status(state['goal_id'], state['current_concept']['id'], 'Active')
        
    logging_service.create_log_entry(
        eventType="P4_Material_Generation",
        conceptId=state['current_concept']['id'],
        textContent=state['llm_output']
    )
    
    return state


def start_remediation_diagnosis(state: ALISState) -> ALISState:
    """
    P5.5, Part 1: Tutor starts diagnosis when knowledge gap is detected.
    """
    llm = get_llm_service()
    
    concept_name = state['current_concept']['name']
    user_prompt = (
        f"[ACTION: DIAGNOSE_GAP] "
        f"The user triggered the 'missing prerequisite' indicator on the concept '{concept_name}'. "
        f"Start the diagnosis."
    )
    
    llm_result = llm.call(TUTOR_PROMPT, user_prompt)
    state['llm_output'] = llm_result
    state['remediation_needed'] = True
    
    logging_service.create_log_entry(
        eventType="P5.5_Gap_Diagnosis",
        conceptId=state['current_concept']['id'],
        textContent=state['llm_output'],
        emotionFeedback="Gap indicator triggered"
    )
    
    return state


def perform_remediation(state: ALISState) -> ALISState:
    """
    P5.5, Part 2: Architect performs path surgery to insert missing concept.
    """
    llm = get_llm_service()
    db = get_db_service()
    
    missing_concept_name = state['user_input']
    user_prompt = (
        f"[ACTION: PERFORM_PATH_SURGERY] "
        f"Perform path surgery. The missing prerequisite is: '{missing_concept_name}'. "
        f"The current path is: {json.dumps(state['path_structure'], ensure_ascii=False)}. "
        f"ALWAYS respond in JSON format with the keys 'path_structure' and 'new_current_concept'."
    )
    
    llm_result = llm.call(ARCHITECT_PROMPT, user_prompt)
    
    new_path = state['path_structure']
    new_current_concept = state['current_concept']

    try:
        parsed_result = json.loads(llm_result)
        new_path_data = parsed_result.get('path_structure', state['path_structure'])
        new_current_concept_data = parsed_result.get('new_current_concept', state['current_concept'])

        new_path = [ConceptDict(**c) for c in new_path_data]
        new_current_concept = ConceptDict(**new_current_concept_data)
        state['llm_output'] = llm_result

    except Exception as e:
        print(f"Error parsing LLM output in perform_remediation: {e}")
        state['llm_output'] = f"Error during path surgery. Please try again. Details: {e}"

    state['path_structure'] = new_path
    state['current_concept'] = new_current_concept
    state['remediation_needed'] = False
    
    if state.get('goal_id') and state.get('goal'):
        state['goal']['path_structure'] = new_path
        db.save_goal(state['goal_id'], state['goal'])

    logging_service.create_log_entry(
        eventType="P5.5_Remediation",
        conceptId=new_current_concept['id'],
        textContent=state['llm_output']
    )
    
    return state


def process_chat(state: ALISState) -> ALISState:
    """
    P5/P7: Tutor responds to chat requests and provides adaptive feedback.
    """
    llm = get_llm_service()
    
    current_topic = state['current_concept'].get('name', 'the current topic')
    user_input = state['user_input']
    user_prompt = (
        f"[ACTION: CHAT_WITH_TUTOR] "
        f"The user asks: '{user_input}'. "
        f"The current topic is: {current_topic}. "
        f"React affectively and helpfully. Also, identify the user's emotion (Frustration, Confusion, Joy, Neutral)."
    )
    
    llm_result = llm.call(TUTOR_PROMPT, user_prompt)
    state['llm_output'] = llm_result
    
    emotion_feedback_match = re.search(r"Emotion:\s*(Frustration|Confusion|Joy|Neutral)", llm_result, re.IGNORECASE)
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
    P6: Curator generates comprehension test questions.
    """
    llm = get_llm_service()
    
    concept_name = state['current_concept']['name']
    required_level = state['current_concept'].get('requiredBloomLevel', 3)
    user_profile = state.get('user_profile', {})
    user_prompt = (
        f"[ACTION: GENERATE_TEST] "
        f"Generate a test for the concept: '{concept_name}'. "
        f"Required Bloom Level: {required_level}. "
        f"User Profile: {json.dumps(user_profile, ensure_ascii=False)}. "
        f"ALWAYS respond in JSON format with a 'test_questions' array."
    )
    
    llm_result = llm.call(CURATOR_PROMPT, user_prompt)
    state['llm_output'] = llm_result
    
    logging_service.create_log_entry(
        eventType="P6_Test_Generation",
        conceptId=state['current_concept']['id'],
        textContent=state['llm_output']
    )
    
    return state


def evaluate_test(state: ALISState) -> ALISState:
    """
    P7: Curator evaluates user's test answers and determines progression.
    """
    llm = get_llm_service()
    db = get_db_service()
    
    goal_id = state['goal_id']
    current_concept = state['current_concept']
    user_profile = state.get('user_profile', {})
    
    try:
        original_test_questions = json.loads(state['llm_output']).get('test_questions', [])
    except Exception:
        original_test_questions = []

    try:
        user_answers = json.loads(state['user_input'])
    except Exception:
        user_answers = {}

    if not original_test_questions:
        state['llm_output'] = "Error: Could not load original test questions for evaluation."
        state['test_evaluation_result'] = {"passed": False, "score": 0, "feedback": "Error during test evaluation.", "recommendation": "Repeat the concept."}
        return state

    evaluation_prompt = (
        f"[ACTION: EVALUATE_TEST] "
        f"Evaluate the user's answers for the test questions on the concept '{current_concept.get('name')}'.\n"
        f"Original questions: {json.dumps(original_test_questions, ensure_ascii=False)}\n\n"
        f"User answers: {json.dumps(user_answers, ensure_ascii=False)}\n\n"
        f"Based on the concept's Bloom's level requirement ({current_concept.get('requiredBloomLevel', 3)}):\n"
        f"1. Provide a score (0-100).\n"
        f"2. Decide if the user passed (passed: true/false). Passing is >70%."
        f"3. Provide constructive and motivational feedback. If failed, be encouraging and suggest specific areas to review.\n"
        f"4. Recommend next steps (Proceed, Repeat, or check prerequisites)."
        f"ALWAYS respond in JSON format with keys: 'score', 'passed', 'feedback', 'recommendation', 'question_results' (list of {{id, correct, explanation}})."
    )
    
    llm_evaluation_result = llm.call(CURATOR_PROMPT, evaluation_prompt)
    
    try:
        eval_data = json.loads(llm_evaluation_result)
        score = eval_data.get('score', 0)
        passed = eval_data.get('passed', False)
        feedback = eval_data.get('feedback', "No specific feedback from LLM.")
        recommendation = eval_data.get('recommendation', "N/A")
        question_results = eval_data.get('question_results', [])
    except Exception as e:
        print(f"Error parsing LLM evaluation result: {e}")
        score, passed, feedback, recommendation, question_results = 0, False, "Error parsing evaluation.", "Review concept.", []

    if goal_id and current_concept:
        new_status = "Mastered" if passed else "Review"
        db.update_concept_status(goal_id, current_concept['id'], new_status)
        current_concept['status'] = new_status
        for concept in state['path_structure']:
            if concept.get('id') == current_concept['id']:
                concept['status'] = new_status
                break

        if passed:
            current_index = next((i for i, c in enumerate(state['path_structure']) if c.get('id') == current_concept['id']), -1)
            next_concept = next((c for c in state['path_structure'][current_index + 1:] if c.get('status') in ['Open', 'Reactivated']), None) if current_index != -1 else None
            state['current_concept'] = next_concept
        
    user_profile['lastTestScore'] = score
    
    # Calculate Cognitive Discrepancy (simplified)
    # High discrepancy if user failed but expected to pass (e.g. high previous scores) - here just based on fail
    kognitive_diskrepanz = "High" if not passed else "Low"
    
    # Emotion Feedback (could be analyzed from user answers if they were text, here simplified)
    emotion_feedback = "Frustration" if not passed else "Satisfaction"

    logging_service.create_log_entry(
        eventType="P6_Test_Evaluation",
        conceptId=current_concept['id'],
        textContent=f"Questions: {json.dumps(original_test_questions)}, Answers: {json.dumps(user_answers)}",
        testScore=score,
        kognitiveDiskrepanz=kognitive_diskrepanz,
        emotionFeedback=emotion_feedback
    )

    state['llm_output'] = feedback
    state['test_evaluation_result'] = {
        "passed": passed, "score": score, "feedback": feedback, 
        "recommendation": recommendation, "question_results": question_results
    }
    state['test_passed'] = passed 

    return state


def generate_prior_knowledge_test(state: ALISState) -> ALISState:
    """
    P2: Assessor generates prior knowledge assessment questions.
    """
    llm = get_llm_service()
    path_summary = json.dumps([c['name'] for c in state.get('path_structure', [])], ensure_ascii=False)
    
    prompt = (
        f"[ACTION: GENERATE_P2_TEST] "
        f"Generate a pre-assessment test for the following learning path: {path_summary}. "
        f"Create 3-5 questions to check which of these concepts the user has already mastered. "
        f"Respond in JSON with a 'questions' array (id, question_text, type)."
    )
    
    response = llm.call(ASSESSOR_PROMPT, prompt)
    
    try:
        data = json.loads(response)
        questions = data.get('questions', [])
    except Exception as e:
        print(f"Error parsing prior knowledge questions: {e}")
        questions = []
        
    state['llm_output'] = json.dumps({'test_questions': questions})
    return state


def evaluate_prior_knowledge_test(state: ALISState) -> ALISState:
    """
    P2: Assessor evaluates prior knowledge and updates path structure.
    """
    llm = get_llm_service()
    db = get_db_service()
    goal_id = state['goal_id']
    path_structure = state.get('path_structure', [])
    
    try:
        original_questions = json.loads(state['llm_output']).get('test_questions', [])
        user_answers = json.loads(state['user_input'])
    except Exception as e:
        print(f"Error parsing inputs for P2 evaluation: {e}")
        return state
        
    prompt = (
        f"[ACTION: EVALUATE_P2_TEST] "
        f"Evaluate the answers for the pre-assessment test.\n"
        f"Questions: {json.dumps(original_questions, ensure_ascii=False)}\n"
        f"Answers: {json.dumps(user_answers, ensure_ascii=False)}\n"
        f"Learning Path: {json.dumps(path_structure, ensure_ascii=False)}\n"
        f"Identify concepts the user has already mastered. "
        f"Respond in JSON with 'mastered_concepts' (list of concept IDs) and 'feedback'."
    )
    
    response = llm.call(ASSESSOR_PROMPT, prompt)
    
    try:
        data = json.loads(response)
        mastered_ids = data.get('mastered_concepts', [])
        feedback = data.get('feedback', "")
        
        for concept in path_structure:
            if concept['id'] in mastered_ids:
                concept['status'] = 'Skipped'
                concept['expertiseSource'] = 'P2 Pre-assessment'
                if goal_id:
                    db.update_concept_status(goal_id, concept['id'], 'Skipped')
                    
        state['llm_output'] = feedback
        state['path_structure'] = path_structure
        
    except Exception as e:
        print(f"Error evaluating prior knowledge: {e}")
        
    return state