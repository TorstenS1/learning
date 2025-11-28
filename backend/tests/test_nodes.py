"""
Unit tests for ALIS agent nodes.
"""
import pytest
import json
from unittest.mock import MagicMock, patch
from backend.agents.nodes import (
    create_goal_path,
    generate_material,
    evaluate_test,
    process_chat
)
from backend.models.state import ALISState


@pytest.fixture
def mock_llm_service():
    with patch('backend.agents.nodes.get_llm_service') as mock:
        mock_llm = MagicMock()
        mock.return_value = mock_llm
        yield mock_llm


@pytest.fixture
def mock_db_service():
    with patch('backend.agents.nodes.get_db_service') as mock:
        mock_db = MagicMock()
        mock.return_value = mock_db
        yield mock_db


@pytest.fixture
def mock_logging_service():
    with patch('backend.agents.nodes.logging_service') as mock:
        yield mock


@pytest.fixture
def sample_state():
    return ALISState(
        user_id='test_user',
        goal_id='test_goal',
        path_structure=[
            {'id': 'c1', 'name': 'Concept 1', 'status': 'Open'},
            {'id': 'c2', 'name': 'Concept 2', 'status': 'Open'}
        ],
        current_concept={'id': 'c1', 'name': 'Concept 1'},
        llm_output='',
        user_input='',
        language='de',
        user_profile={'stylePreference': 'Analogy-based'}
    )


class TestCreateGoalPath:
    def test_create_goal_path_success(self, mock_llm_service, mock_db_service, mock_logging_service):
        # Setup
        mock_llm_service.call.return_value = '''{
            "goal_contract": {
                "goal": "Learn Python",
                "specific": "Learn basics",
                "measurable": "Complete 5 exercises",
                "achievable": "Yes",
                "relevant": "For career",
                "time_bound": "2 weeks"
            },
            "path_structure": [
                {"id": "K1", "name": "Variables", "status": "Open", "requiredBloomLevel": 2}
            ]
        }'''
        
        state = ALISState(
            user_id='test_user',
            user_input='I want to learn Python',
            language='en'
        )
        
        # Execute
        result = create_goal_path(state)
        
        # Verify
        assert result['goal_id'] is not None
        assert len(result['path_structure']) == 1
        assert result['path_structure'][0]['name'] == 'Variables'
        mock_db_service.save_goal.assert_called_once()
        mock_logging_service.create_log_entry.assert_called_once()


class TestGenerateMaterial:
    def test_generate_material_success(self, mock_llm_service, mock_db_service, mock_logging_service, sample_state):
        # Setup
        mock_llm_service.call.return_value = 'Learning material about Concept 1...'
        
        # Execute
        result = generate_material(sample_state)
        
        # Verify
        assert result['llm_output'] == 'Learning material about Concept 1...'
        mock_llm_service.call.assert_called_once()
        mock_db_service.update_concept_status.assert_called_once_with(
            'test_goal', 'c1', 'Active'
        )
        mock_logging_service.create_log_entry.assert_called_once()
    
    def test_generate_material_with_failed_test(self, mock_llm_service, mock_db_service, mock_logging_service, sample_state):
        # Setup - Add failed test result
        sample_state['test_evaluation_result'] = {
            'passed': False,
            'feedback': 'You struggled with loops'
        }
        mock_llm_service.call.return_value = 'Remediation material...'
        
        # Execute
        result = generate_material(sample_state)
        
        # Verify - Should include remediation context
        call_args = mock_llm_service.call.call_args[0]
        assert 'previously failed a test' in call_args[1]
        assert 'You struggled with loops' in call_args[1]


class TestEvaluateTest:
    def test_evaluate_test_passed(self, mock_llm_service, mock_db_service, mock_logging_service, sample_state):
        # Setup
        questions = [{'id': 'q1', 'question_text': 'What is a variable?'}]
        answers = {'q1': 'A container for data'}
        
        sample_state['llm_output'] = json.dumps({'test_questions': questions})
        sample_state['user_input'] = json.dumps(answers)
    
        mock_llm_service.call.return_value = '''{
            "score": 85,
            "passed": true,
            "feedback": "Great job!",
            "recommendation": "Proceed",
            "question_results": [
                {"id": "q1", "correct": true, "explanation": "Correct!"}
            ]
        }'''
    
        # Execute
        result = evaluate_test(sample_state)
    
        # Verify
        assert result['test_evaluation_result']['passed'] == True
        assert result['test_evaluation_result']['score'] == 85
        assert result['current_concept']['id'] == 'c2'  # Should move to next concept
        mock_db_service.update_concept_status.assert_called_with('test_goal', 'c1', 'Mastered')
        
        # Verify logging with correct emotion
        log_call = mock_logging_service.create_log_entry.call_args
        assert log_call[1]['emotionFeedback'] == 'Satisfaction'
        assert log_call[1]['kognitiveDiskrepanz'] == 'Low'
    
    def test_evaluate_test_failed(self, mock_llm_service, mock_db_service, mock_logging_service, sample_state):
        # Setup
        questions = [{'id': 'q1', 'question_text': 'What is a variable?'}]
        answers = {'q1': 'Wrong answer'}
        
        sample_state['llm_output'] = json.dumps({'test_questions': questions})
        sample_state['user_input'] = json.dumps(answers)
    
        mock_llm_service.call.return_value = '''{
            "score": 45,
            "passed": false,
            "feedback": "Needs improvement",
            "recommendation": "Review material",
            "question_results": [
                {"id": "q1", "correct": false, "explanation": "Not quite"}
            ]
        }'''
    
        # Execute
        result = evaluate_test(sample_state)
    
        # Verify
        assert result['test_evaluation_result']['passed'] == False
        assert result['test_evaluation_result']['score'] == 45
        assert result['current_concept']['id'] == 'c1'  # Should stay on same concept
        mock_db_service.update_concept_status.assert_called_with('test_goal', 'c1', 'Review')
        
        # Verify logging with frustration emotion
        log_call = mock_logging_service.create_log_entry.call_args
        assert log_call[1]['emotionFeedback'] == 'Frustration'
        assert log_call[1]['kognitiveDiskrepanz'] == 'High'


class TestProcessChat:
    def test_process_chat(self, mock_llm_service, sample_state):
        # Setup
        sample_state['user_input'] = 'Can you explain variables?'
        sample_state['tutor_chat'] = []
        mock_llm_service.call.return_value = 'A variable is a container for storing data.'
        
        # Execute
        result = process_chat(sample_state)
        
        # Verify
        assert result['llm_output'] == 'A variable is a container for storing data.'
