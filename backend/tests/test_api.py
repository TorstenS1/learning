import pytest
from unittest.mock import MagicMock, patch
from backend.app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def mock_session_manager():
    # Patch where it is imported/used. Since it's imported inside the function in app.py,
    # we patch the source in session_service.
    with patch('backend.services.session_service.get_session_manager') as mock_get:
        mock_manager = MagicMock()
        mock_get.return_value = mock_manager
        yield mock_manager

@pytest.fixture
def mock_workflow():
    with patch('backend.app.workflow') as mock:
        yield mock

@pytest.fixture
def mock_llm_service():
    with patch('backend.app.llm_service') as mock:
        yield mock


class TestHealthEndpoint:
    def test_health_check(self, client):
        response = client.get('/api/health')
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'healthy'
        assert 'service' in data
        assert 'version' in data


class TestSessionManagement:
    def test_save_session_endpoint(self, client, mock_session_manager):
        # Setup
        mock_session_manager.save_session.return_value = 'session_id_123'
        
        payload = {
            'userId': 'user1',
            'sessionData': {'goalId': 'g1'},
            'sessionName': 'Test Session'
        }
        
        # Execute
        response = client.post('/api/save_session', json=payload)
        
        # Verify
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'success'
        assert data['data']['sessionId'] == 'session_id_123'
        
        mock_session_manager.save_session.assert_called_once_with(
            'user1', 
            {'goalId': 'g1'}, 
            'Test Session'
        )

    def test_list_sessions_endpoint(self, client, mock_session_manager):
        # Setup
        mock_session_manager.list_sessions.return_value = [
            {'session_name': 'S1', 'goal_id': 'g1'}
        ]
        
        payload = {'userId': 'user1'}
        
        # Execute
        response = client.post('/api/list_sessions', json=payload)
        
        # Verify
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'success'
        assert len(data['data']['sessions']) == 1
        assert data['data']['sessions'][0]['session_name'] == 'S1'

    def test_load_session_endpoint(self, client, mock_session_manager):
        # Setup
        mock_session_manager.load_session.return_value = {
            'goal_id': 'g1',
            'phase': 'P5_LEARNING',
            'path_structure': []
        }
        
        payload = {'userId': 'user1', 'goalId': 'g1'}
        
        # Execute
        response = client.post('/api/load_session', json=payload)
        
        # Verify
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'success'
        assert data['data']['goal_id'] == 'g1'

    def test_save_session_missing_fields(self, client):
        # Execute - Missing sessionData
        payload = {'userId': 'user1'}
        response = client.post('/api/save_session', json=payload)
        
        # Verify
        assert response.status_code == 400
        data = response.get_json()
        assert data['status'] == 'error'


class TestGoalCreation:
    @patch('backend.app.run_workflow_step')
    def test_start_goal_success(self, mock_run_workflow, client):
        # Setup
        mock_run_workflow.return_value = {
            'P1_P3_Goal_Path_Creation': {
                'goal_id': 'new_goal_123',
                'path_structure': [
                    {'id': 'c1', 'name': 'Concept 1', 'status': 'Open'}
                ],
                'llm_output': 'Goal created successfully'
            }
        }
        
        payload = {
            'userId': 'user1',
            'userInput': 'I want to learn Python',
            'language': 'en'
        }
        
        # Execute
        response = client.post('/api/start_goal', json=payload)
        
        # Verify
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'success'
        assert data['data']['goal_id'] == 'new_goal_123'
        assert len(data['data']['path_structure']) == 1

    def test_start_goal_missing_input(self, client):
        # Execute - Missing userInput
        payload = {'userId': 'user1'}
        response = client.post('/api/start_goal', json=payload)
        
        # Verify
        assert response.status_code == 400
        data = response.get_json()
        assert data['status'] == 'error'


class TestMaterialGeneration:
    @patch('backend.app.run_workflow_step')
    def test_get_material_success(self, mock_run_workflow, client):
        # Setup
        mock_run_workflow.return_value = {
            'P4_Material_Generation': {
                'llm_output': 'Here is the learning material...'
            }
        }
        
        payload = {
            'userId': 'user1',
            'goalId': 'g1',
            'pathStructure': [{'id': 'c1', 'name': 'Concept 1'}],
            'currentConcept': {'id': 'c1', 'name': 'Concept 1'},
            'userProfile': {}
        }
        
        # Execute
        response = client.post('/api/get_material', json=payload)
        
        # Verify
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'success'
        assert 'learning material' in data['data']['llm_output']


class TestTestEvaluation:
    @patch('backend.agents.nodes.evaluate_test')
    def test_submit_test_success(self, mock_evaluate, client):
        # Setup
        mock_evaluate.return_value = {
            'llm_output': 'Test evaluated',
            'test_evaluation_result': {
                'passed': True,
                'score': 85,
                'feedback': 'Great job!'
            },
            'path_structure': [{'id': 'c1', 'status': 'Mastered'}],
            'current_concept': {'id': 'c2', 'name': 'Concept 2'}
        }
        
        payload = {
            'userId': 'user1',
            'goalId': 'g1',
            'currentConcept': {'id': 'c1', 'name': 'Concept 1'},
            'testQuestions': [{'id': 'q1', 'question_text': 'What is X?'}],
            'userAnswers': {'q1': 'Answer'},
            'pathStructure': [{'id': 'c1', 'status': 'Active'}]
        }
        
        # Execute
        response = client.post('/api/submit_test', json=payload)
        
        # Verify
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'success'
        assert data['data']['evaluation_result']['passed'] == True
        assert data['data']['evaluation_result']['score'] == 85


class TestErrorHandling:
    def test_404_error(self, client):
        response = client.get('/api/nonexistent')
        assert response.status_code == 404
        data = response.get_json()
        assert data['status'] == 'error'
    
    @patch('backend.app.run_workflow_step')
    def test_500_error_handling(self, mock_run_workflow, client):
        # Setup - Simulate an exception
        mock_run_workflow.side_effect = Exception('Database error')
        
        payload = {
            'userId': 'user1',
            'userInput': 'Test',
            'language': 'en'
        }
        
        # Execute
        response = client.post('/api/start_goal', json=payload)
        
        # Verify
        assert response.status_code == 500
        data = response.get_json()
        assert data['status'] == 'error'

