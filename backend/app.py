"""
Flask REST API for ALIS backend.
Provides HTTP endpoints for the React frontend to interact with the LangGraph workflow.
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import traceback
import json
from typing import Dict, Any

from backend.config.settings import HOST, PORT, DEBUG, CORS_ORIGINS
from backend.models.state import ALISState
from backend.workflows.alis_graph import get_workflow
from backend.services.llm_service import get_llm_service
from backend.services.db_service import get_db_service


# Initialize Flask app
app = Flask(__name__)

# Configure CORS
CORS(app, resources={
    r"/api/*": {
        "origins": CORS_ORIGINS,
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

# Initialize services
llm_service = get_llm_service(use_simulation=False)
db_service = get_db_service()
workflow = get_workflow()


def create_initial_state(payload: Dict[str, Any]) -> ALISState:
    """
    Create initial ALIS state from request payload.
    
    Args:
        payload: Request JSON data
        
    Returns:
        ALISState dictionary
    """
    return ALISState(
        user_id=payload.get('userId', 'anonymous_user'),
        goal_id=payload.get('goalId', None),
        path_structure=payload.get('pathStructure', []),
        current_concept=payload.get('currentConcept', {}),
        llm_output="",
        user_input=payload.get('userInput', ''),
        remediation_needed=payload.get('remediationNeeded', False),
        language=payload.get('language', 'de'),  # Extract language from payload
        next_step=payload.get('nextStep', 'P1_P3_Goal_Path_Creation'),  # Routing parameter
        user_profile=payload.get('userProfile', {
            'stylePreference': 'Analogien-basiert',
            'paceWPM': 180
        })
    )


def run_workflow_step(state: ALISState, start_node: str) -> Dict[str, Any]:
    """
    Execute a workflow step starting from a specific node.
    
    Args:
        state: Initial ALIS state
        start_node: Name of the node to start from
        
    Returns:
        Final state after workflow execution
    """
    final_state = None
    
    # Stream through the workflow
    for step_output in workflow.stream(state, {"recursion_limit": 50}):
        final_state = step_output
    
    return final_state


@app.route('/api/health', methods=['GET'])
def health_check():
    """
    Health check endpoint.
    
    Returns:
        JSON with service status
    """
    return jsonify({
        'status': 'healthy',
        'service': 'ALIS Backend',
        'version': '1.0.0',
        'simulation_mode': llm_service.use_simulation
    }), 200


@app.route('/api/start_goal', methods=['POST'])
def start_goal():
    """
    P1/P3: Start goal setting and path creation.
    
    Expected payload:
        {
            "userId": str,
            "userInput": str (the learning goal),
            "userProfile": dict (optional)
        }
    
    Returns:
        JSON with goal, path structure, and current concept
    """
    try:
        payload = request.get_json()
        
        if not payload or 'userInput' not in payload:
            return jsonify({
                'status': 'error',
                'message': 'Missing required field: userInput'
            }), 400
        
        # Create initial state
        initial_state = create_initial_state(payload)
        
        # Run workflow from P1_P3_Goal_Path_Creation
        final_state_output = run_workflow_step(initial_state, "P1_P3_Goal_Path_Creation")
        
        # Extract the final state from the last node output
        if final_state_output:
            # LangGraph returns dict with node names as keys in stream output
            # We need the ALISState itself from the last step
            result_state = ALISState(**final_state_output[list(final_state_output.keys())[-1]])
        else:
            result_state = initial_state # Fallback
        
        return jsonify({
            'status': 'success',
            'data': {
                'userId': result_state.get('user_id'),
                'goalId': result_state.get('goal_id', 'G-TEMP-001'),
                'llm_output': result_state.get('llm_output'),
                'path_structure': result_state.get('path_structure'),
                'current_concept': result_state.get('current_concept'),
                'user_profile': result_state.get('user_profile')
            }
        }), 200
        
    except Exception as e:
        app.logger.error(f"Error in start_goal: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'message': f'Internal server error: {str(e)}'
        }), 500


@app.route('/api/get_material', methods=['POST'])
def get_material():
    """
    P4: Generate learning material for current concept.
    
    Expected payload:
        {
            "userId": str,
            "goalId": str,
            "pathStructure": list,
            "currentConcept": dict,
            "userProfile": dict
        }
    
    Returns:
        JSON with generated material
    """
    try:
        payload = request.get_json()
        
        if not payload or 'currentConcept' not in payload:
            return jsonify({
                'status': 'error',
                'message': 'Missing required field: currentConcept'
            }), 400
        
        initial_state = create_initial_state(payload)
        initial_state['next_step'] = 'P4_Material_Generation'  # Route to material generation
        
        # Run workflow from P4_Material_Generation
        final_state_output = run_workflow_step(initial_state, "P4_Material_Generation")

        if final_state_output:
            result_state = ALISState(**final_state_output[list(final_state_output.keys())[-1]])
        else:
            result_state = initial_state
        
        return jsonify({
            'status': 'success',
            'data': {
                'llm_output': result_state.get('llm_output'),
                'path_structure': result_state.get('path_structure'), # Path might be updated by P5_5
                'current_concept': result_state.get('current_concept') # Current concept might change after remediation
            }
        }), 200
        
    except Exception as e:
        app.logger.error(f"Error in get_material: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'message': f'Internal server error: {str(e)}'
        }), 500


@app.route('/api/chat', methods=['POST'])
def chat():
    """
    P5: Process chat message with tutor.
    
    Expected payload:
        {
            "userId": str,
            "goalId": str,
            "userInput": str (chat message),
            "currentConcept": dict
        }
    
    Returns:
        JSON with tutor response
    """
    try:
        payload = request.get_json()
        
        if not payload or 'userInput' not in payload:
            return jsonify({
                'status': 'error',
                'message': 'Missing required field: userInput'
            }), 400
        
        initial_state = create_initial_state(payload)
        initial_state['next_step'] = 'P5_Chat_Tutor'  # Route to chat
        
        # Run workflow from P5_Chat_Tutor
        final_state_output = run_workflow_step(initial_state, "P5_Chat_Tutor")

        if final_state_output:
            result_state = ALISState(**final_state_output[list(final_state_output.keys())[-1]])
        else:
            result_state = initial_state
        
        return jsonify({
            'status': 'success',
            'data': {
                'llm_output': result_state.get('llm_output')
            }
        }), 200
        
    except Exception as e:
        app.logger.error(f"Error in chat: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'message': f'Internal server error: {str(e)}'
        }), 500


@app.route('/api/diagnose_luecke', methods=['POST'])
def diagnose_luecke():
    """
    P5.5 Part 1: Start gap diagnosis.
    
    Expected payload:
        {
            "userId": str,
            "goalId": str,
            "pathStructure": list,
            "currentConcept": dict
        }
    
    Returns:
        JSON with diagnosis prompt
    """
    try:
        payload = request.get_json()
        
        if not payload or 'currentConcept' not in payload:
            return jsonify({
                'status': 'error',
                'message': 'Missing required field: currentConcept'
            }), 400
        
        initial_state = create_initial_state(payload)
        initial_state['next_step'] = 'P5_5_Diagnosis'  # Route to diagnosis
        
        # Run workflow from P5_5_Diagnosis
        final_state_output = run_workflow_step(initial_state, "P5_5_Diagnosis")

        if final_state_output:
            result_state = ALISState(**final_state_output[list(final_state_output.keys())[-1]])
        else:
            result_state = initial_state
        
        return jsonify({
            'status': 'success',
            'data': {
                'llm_output': result_state.get('llm_output'),
                'remediation_needed': result_state.get('remediation_needed')
            }
        }), 200
        
    except Exception as e:
        app.logger.error(f"Error in diagnose_luecke: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'message': f'Internal server error: {str(e)}'
        }), 500


@app.route('/api/perform_remediation', methods=['POST'])
def perform_remediation():
    """
    P5.5 Part 2: Perform path surgery.
    
    Expected payload:
        {
            "userId": str,
            "goalId": str,
            "userInput": str (missing concept name),
            "pathStructure": list,
            "currentConcept": dict,
            "remediationNeeded": true
        }
    
    Returns:
        JSON with updated path structure
    """
    try:
        payload = request.get_json()
        
        if not payload or 'userInput' not in payload:
            return jsonify({
                'status': 'error',
                'message': 'Missing required field: userInput'
            }), 400
        
        initial_state = create_initial_state(payload)
        
        # Call the node directly
        from backend.agents.nodes import perform_remediation
        result_state = perform_remediation(initial_state)
        
        return jsonify({
            'status': 'success',
            'data': {
                'llm_output': result_state.get('llm_output'),
                'path_structure': result_state.get('path_structure'),
                'current_concept': result_state.get('current_concept'),
                'remediation_needed': result_state.get('remediation_needed')
            }
        }), 200
        
    except Exception as e:
        app.logger.error(f"Error in perform_remediation: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'message': f'Internal server error: {str(e)}'
        }), 500


@app.route('/api/generate_test', methods=['POST'])
def generate_test():
    """
    P6: Generate test questions.
    
    Expected payload:
        {
            "userId": str,
            "goalId": str,
            "currentConcept": dict,
            "userProfile": dict
        }
    
    Returns:
        JSON with test questions
    """
    try:
        payload = request.get_json()
        
        if not payload or 'currentConcept' not in payload:
            return jsonify({
                'status': 'error',
                'message': 'Missing required field: currentConcept'
            }), 400
        
        initial_state = create_initial_state(payload)
        
        # Call the node directly
        from backend.agents.nodes import generate_test
        result_state = generate_test(initial_state)
        
        return jsonify({
            'status': 'success',
            'data': {
                'llm_output': result_state.get('llm_output')
            }
        }), 200
        
    except Exception as e:
        app.logger.error(f"Error in generate_test: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'message': f'Internal server error: {str(e)}'
        }), 500


@app.route('/api/submit_test', methods=['POST'])
def submit_test():
    """
    P6: Submit test answers for evaluation.
    
    Expected payload:
        {
            "userId": str,
            "goalId": str,
            "currentConcept": dict,
            "testQuestions": list,    # Original questions generated by LLM
            "userAnswers": dict       # User's answers keyed by question ID
        }
    
    Returns:
        JSON with LLM's evaluation output and structured evaluation result
    """
    try:
        payload = request.get_json()
        
        if not payload or 'currentConcept' not in payload or 'testQuestions' not in payload or 'userAnswers' not in payload:
            return jsonify({
                'status': 'error',
                'message': 'Missing required fields for test submission'
            }), 400
        
        # Create initial state. We need to pass the test questions and user answers
        # in a way that the evaluate_test node can access them.
        initial_state = ALISState(
            user_id=payload.get('userId', 'anonymous_user'),
            goal_id=payload.get('goalId', None),
            path_structure=payload.get('pathStructure', []), # Path structure is needed for progression logic
            current_concept=payload.get('currentConcept', {}),
            llm_output=json.dumps({"test_questions": payload.get('testQuestions')}), # Original questions for agent
            user_input=json.dumps(payload.get('userAnswers')), # User answers for agent
            remediation_needed=False,
            user_profile=payload.get('userProfile', {
                'stylePreference': 'Analogien-basiert',
                'paceWPM': 180
            })
        )
        
        # Call the node directly
        from backend.agents.nodes import evaluate_test
        result_state = evaluate_test(initial_state)
        
        # The evaluate_test node is expected to return structured evaluation
        # and human-readable feedback in llm_output, and update path_structure/current_concept
        return jsonify({
            'status': 'success',
            'data': {
                'llm_output': result_state.get('llm_output'),
                'evaluation_result': result_state.get('test_evaluation_result'), # Expecting this key from evaluate_test
                'path_structure': result_state.get('path_structure'), # Updated path for frontend
                'current_concept': result_state.get('current_concept') # Updated concept for frontend
            }
        }), 200
        
    except Exception as e:
        app.logger.error(f"Error in submit_test: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'message': f'Internal server error: {str(e)}'
        }), 500

        return jsonify({
            'status': 'error',
            'message': f'Internal server error: {str(e)}'
        }), 500


@app.route('/api/generate_prior_knowledge_test', methods=['POST'])
def generate_prior_knowledge_test_endpoint():
    """
    P2: Generate prior knowledge assessment questions.
    """
    try:
        payload = request.get_json()
        if not payload or 'goalId' not in payload or 'pathStructure' not in payload:
            return jsonify({'status': 'error', 'message': 'Missing goalId or pathStructure'}), 400
            
        initial_state = ALISState(
            user_id=payload.get('userId', 'anonymous_user'),
            goal_id=payload.get('goalId'),
            path_structure=payload.get('pathStructure', []),
            current_concept={},
            llm_output="",
            user_input="",
            remediation_needed=False,
            user_profile=payload.get('userProfile', {})
        )
        
        from backend.agents.nodes import generate_prior_knowledge_test
        result_state = generate_prior_knowledge_test(initial_state)
        
        return jsonify({
            'status': 'success',
            'llm_output': result_state.get('llm_output')
        }), 200
    except Exception as e:
        app.logger.error(f"Error in generate_prior_knowledge_test: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/evaluate_prior_knowledge_test', methods=['POST'])
def evaluate_prior_knowledge_test_endpoint():
    """
    P2: Evaluate prior knowledge and update path.
    """
    try:
        payload = request.get_json()
        if not payload or 'testQuestions' not in payload or 'userAnswers' not in payload:
            return jsonify({'status': 'error', 'message': 'Missing test data'}), 400
            
        initial_state = ALISState(
            user_id=payload.get('userId', 'anonymous_user'),
            goal_id=payload.get('goalId'),
            path_structure=payload.get('pathStructure', []),
            current_concept={},
            llm_output=json.dumps({"test_questions": payload.get('testQuestions')}),
            user_input=json.dumps(payload.get('userAnswers')),
            remediation_needed=False,
            user_profile=payload.get('userProfile', {})
        )
        
        from backend.agents.nodes import evaluate_prior_knowledge_test
        result_state = evaluate_prior_knowledge_test(initial_state)
        
        return jsonify({
            'status': 'success',
            'llm_output': result_state.get('llm_output'),
            'path_structure': result_state.get('path_structure')
        }), 200
    except Exception as e:
        app.logger.error(f"Error in evaluate_prior_knowledge_test: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({
        'status': 'error',
        'message': 'Endpoint not found'
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    app.logger.error(f"Internal server error: {str(error)}")
    return jsonify({
        'status': 'error',
        'message': 'Internal server error'
    }), 500


@app.route('/api/save_session', methods=['POST'])
def save_session():
    """
    Save current learning session.
    
    Expected payload:
        {
            "userId": str,
            "sessionData": dict (current app state)
        }
    
    Returns:
        JSON with session ID
    """
    try:
        from backend.services.session_service import get_session_manager
        
        payload = request.get_json()
        
        if not payload or 'userId' not in payload or 'sessionData' not in payload:
            return jsonify({
                'status': 'error',
                'message': 'Missing required fields: userId, sessionData'
            }), 400
        
        session_manager = get_session_manager()
        session_id = session_manager.save_session(
            payload['userId'],
            payload['sessionData'],
            payload.get('sessionName')  # Optional custom name
        )
        
        return jsonify({
            'status': 'success',
            'data': {
                'sessionId': session_id,
                'message': 'Session saved successfully'
            }
        }), 200
        
    except Exception as error:
        app.logger.error(f"Error in save_session: {str(error)}")
        app.logger.error(traceback.format_exc())
        return jsonify({
            'status': 'error',
            'message': str(error)
        }), 500


@app.route('/api/load_session', methods=['POST'])
def load_session():
    """
    Load saved learning session.
    
    Expected payload:
        {
            "userId": str,
            "goalId": str (optional)
        }
    
    Returns:
        JSON with session data
    """
    try:
        from backend.services.session_service import get_session_manager
        
        payload = request.get_json()
        
        if not payload or 'userId' not in payload:
            return jsonify({
                'status': 'error',
                'message': 'Missing required field: userId'
            }), 400
        
        session_manager = get_session_manager()
        session_data = session_manager.load_session(
            payload['userId'],
            payload.get('goalId')
        )
        
        if session_data:
            return jsonify({
                'status': 'success',
                'data': session_data
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': 'No session found'
            }), 404
        
    except Exception as error:
        app.logger.error(f"Error in load_session: {str(error)}")
        app.logger.error(traceback.format_exc())
        return jsonify({
            'status': 'error',
            'message': str(error)
        }), 500


@app.route('/api/list_sessions', methods=['POST'])
def list_sessions():
    """
    List all sessions for a user.
    
    Expected payload:
        {
            "userId": str
        }
    
    Returns:
        JSON with list of sessions
    """
    try:
        from backend.services.session_service import get_session_manager
        
        payload = request.get_json()
        
        if not payload or 'userId' not in payload:
            return jsonify({
                'status': 'error',
                'message': 'Missing required field: userId'
            }), 400
        
        session_manager = get_session_manager()
        sessions = session_manager.list_sessions(payload['userId'])
        
        return jsonify({
            'status': 'success',
            'data': {
                'sessions': sessions
            }
        }), 200
        
    except Exception as error:
        app.logger.error(f"Error in list_sessions: {str(error)}")
        app.logger.error(traceback.format_exc())
        return jsonify({
            'status': 'error',
            'message': str(error)
        }), 500


# Error handlers


if __name__ == '__main__':
    print("=" * 60)
    print("🚀 ALIS Backend Server Starting...")
    print("=" * 60)
    print(f"Host: {HOST}")
    print(f"Port: {PORT}")
    print(f"Debug: {DEBUG}")
    print(f"Simulation Mode: {llm_service.use_simulation}")
    print(f"CORS Origins: {CORS_ORIGINS}")
    print("=" * 60)
    print("\nAvailable Endpoints:")
    print("  GET  /api/health")
    print("  POST /api/start_goal")
    print("  POST /api/get_material")
    print("  POST /api/chat")
    print("  POST /api/diagnose_luecke")
    print("  POST /api/perform_remediation")
    print("  POST /api/generate_test")
    print("=" * 60)
    
    app.run(host=HOST, port=PORT, debug=DEBUG)
