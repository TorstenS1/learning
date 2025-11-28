import pytest
from unittest.mock import MagicMock, patch
from backend.services.session_service import SessionManager

@pytest.fixture
def mock_db_service():
    with patch('backend.services.session_service.get_db_service') as mock:
        yield mock

def test_save_session(mock_db_service):
    # Setup
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_db_service.return_value.db = {'sessions': mock_collection}
    mock_collection.update_one.return_value.upserted_id = 'new_id'
    
    manager = SessionManager()
    session_data = {
        'goalId': 'goal1',
        'goalName': 'Learn Python',
        'phase': 'P1',
        'language': 'en'
    }
    
    # Execute
    result = manager.save_session('user1', session_data, 'My Session')
    
    # Verify
    assert result == 'new_id'
    mock_collection.update_one.assert_called_once()
    args, kwargs = mock_collection.update_one.call_args
    assert args[0] == {'user_id': 'user1', 'goal_id': 'goal1'}
    assert kwargs['upsert'] == True
    assert args[1]['$set']['session_name'] == 'My Session'
    assert args[1]['$set']['goal_name'] == 'Learn Python'

def test_save_session_default_name(mock_db_service):
    # Setup
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_db_service.return_value.db = {'sessions': mock_collection}
    mock_collection.update_one.return_value.upserted_id = 'new_id'
    
    manager = SessionManager()
    session_data = {
        'goalId': 'goal1',
        'goalName': 'Learn Python',
        'phase': 'P1'
    }
    
    # Execute - No session name provided
    manager.save_session('user1', session_data)
    
    # Verify
    args, _ = mock_collection.update_one.call_args
    assert args[1]['$set']['session_name'] == 'Learn Python'

def test_list_sessions(mock_db_service):
    # Setup
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_db_service.return_value.db = {'sessions': mock_collection}
    
    mock_cursor = MagicMock()
    # Mock iterator behavior for the cursor
    sessions_data = [
        {
            'goal_id': 'g1',
            'session_name': 'S1',
            'goal_name': 'G1',
            'timestamp': '2025-01-01',
            'phase': 'P1',
            'current_concept': {'name': 'C1'}
        },
        {
            'goal_id': 'g2',
            'session_name': 'S2',
            'goal_name': 'G2',
            'timestamp': '2025-01-02',
            'phase': 'P2',
            'current_concept': None
        }
    ]
    mock_cursor.__iter__.return_value = iter(sessions_data)
    mock_collection.find.return_value.sort.return_value = mock_cursor
    
    manager = SessionManager()
    
    # Execute
    result = manager.list_sessions('user1')
    
    # Verify
    assert len(result) == 2
    assert result[0]['session_name'] == 'S1'
    assert result[0]['current_concept'] == 'C1'
    assert result[1]['session_name'] == 'S2'
    assert result[1]['current_concept'] == 'Unknown' # Testing the None handling fix

def test_load_session(mock_db_service):
    # Setup
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_db_service.return_value.db = {'sessions': mock_collection}
    
    mock_collection.find_one.return_value = {
        '_id': 'mongo_id',
        'goal_id': 'g1',
        'session_name': 'S1'
    }
    
    manager = SessionManager()
    
    # Execute
    result = manager.load_session('user1', 'g1')
    
    # Verify
    assert result['goal_id'] == 'g1'
    assert '_id' not in result # Should be removed
