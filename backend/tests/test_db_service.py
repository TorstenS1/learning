import pytest
from unittest.mock import patch, MagicMock
from pymongo.errors import ConnectionFailure, PyMongoError
from bson.objectid import ObjectId

from backend.services.db_service import MongoDBService, get_db_service, serialize_object_id, deserialize_object_id
from backend.models.state import UserProfile, Goal, LogEntry, ConceptDict

# Mock the settings for MongoDB URI and DB Name
@pytest.fixture(autouse=True)
def mock_settings():
    with patch('backend.config.settings.MONGODB_URI', 'mongodb://mock-host:27017/'), \
         patch('backend.config.settings.MONGODB_DB_NAME', 'test_db'):
        yield

# Fixture to mock MongoClient for all tests
@pytest.fixture
def mock_mongo_client():
    with patch('pymongo.MongoClient') as mock_client_class:
        mock_client_instance = MagicMock()
        mock_client_class.return_value = mock_client_instance
        yield mock_client_instance

@pytest.fixture
def db_service_instance(mock_mongo_client):
    # Ensure a fresh instance for each test
    service = MongoDBService()
    # Mock successful connection if it wasn't already by fixture
    if not service.client:
        service._connect()
    yield service
    # Ensure connection is closed after test
    service.close_connection()

def test_db_service_connect_success(mock_mongo_client):
    """Test successful connection to MongoDB."""
    service = MongoDBService()
    mock_mongo_client.assert_called_once_with('mongodb://mock-host:27017/')
    assert service.client is not None
    assert service.db is not None
    assert service.db.name == 'test_db'
    service.client.admin.command.assert_called_once_with('ismaster')

def test_db_service_connect_failure():
    """Test connection failure to MongoDB."""
    with patch('pymongo.MongoClient', side_effect=ConnectionFailure("Test Connection Failed")):
        service = MongoDBService()
        assert service.client is None
        assert service.db is None

def test_get_db_service_singleton(db_service_instance):
    """Test that get_db_service returns a singleton instance."""
    service1 = get_db_service()
    service2 = get_db_service()
    assert service1 is service2
    # Reset global instance for other tests that might need a fresh one
    get_db_service.cache_clear() # If get_db_service was memoized, clear cache
    # This might require more elaborate global state management for actual singletons in tests.
    # For now, rely on fixture providing a fresh mocked client.


def test_save_user_profile(db_service_instance, mock_mongo_client):
    """Test saving a user profile."""
    mock_collection = mock_mongo_client.return_value.test_db.user_profiles
    user_id = "test_user_1"
    profile_data: UserProfile = {"stylePreference": "visual", "paceWPM": 200}

    db_service_instance.save_user_profile(user_id, profile_data)
    
    expected_profile = profile_data.copy()
    expected_profile["_id"] = user_id
    mock_collection.replace_one.assert_called_once_with({"_id": user_id}, expected_profile, upsert=True)

def test_get_user_profile(db_service_instance, mock_mongo_client):
    """Test retrieving a user profile."""
    mock_collection = mock_mongo_client.return_value.test_db.user_profiles
    user_id = "test_user_1"
    stored_profile = {"_id": user_id, "stylePreference": "visual", "paceWPM": 200}
    mock_collection.find_one.return_value = stored_profile

    profile = db_service_instance.get_user_profile(user_id)
    assert profile == UserProfile(stylePreference="visual", paceWPM=200, _id=user_id) # _id added by serialize
    mock_collection.find_one.assert_called_once_with({"_id": user_id})

def test_get_user_profile_not_found(db_service_instance, mock_mongo_client):
    """Test retrieving a non-existent user profile."""
    mock_collection = mock_mongo_client.return_value.test_db.user_profiles
    mock_collection.find_one.return_value = None

    profile = db_service_instance.get_user_profile("non_existent_user")
    assert profile is None

def test_save_goal(db_service_instance, mock_mongo_client):
    """Test saving a learning goal."""
    mock_collection = mock_mongo_client.return_value.test_db.goals
    goal_id = "test_goal_1"
    goal_data: Goal = {"goalId": goal_id, "name": "Learn Python", "status": "In Arbeit"}

    db_service_instance.save_goal(goal_id, goal_data)
    
    expected_goal = goal_data.copy()
    expected_goal["_id"] = goal_id
    mock_collection.replace_one.assert_called_once_with({"_id": goal_id}, expected_goal, upsert=True)

def test_get_goal(db_service_instance, mock_mongo_client):
    """Test retrieving a learning goal."""
    mock_collection = mock_mongo_client.return_value.test_db.goals
    goal_id = "test_goal_1"
    stored_goal = {"_id": goal_id, "name": "Learn Python", "status": "In Arbeit"}
    mock_collection.find_one.return_value = stored_goal

    goal = db_service_instance.get_goal(goal_id)
    assert goal == Goal(goalId=goal_id, name="Learn Python", status="In Arbeit", _id=goal_id)
    mock_collection.find_one.assert_called_once_with({"_id": goal_id})

def test_save_log_entry(db_service_instance, mock_mongo_client):
    """Test saving a log entry."""
    mock_collection = mock_mongo_client.return_value.test_db.logs
    log_entry_data: LogEntry = {"eventType": "P1_Zielsetzung", "textContent": "User set goal"}

    db_service_instance.save_log_entry(log_entry_data)
    mock_collection.insert_one.assert_called_once_with(log_entry_data)

def test_update_concept_status(db_service_instance, mock_mongo_client):
    """Test updating the status of a concept within a goal's path structure."""
    mock_collection = mock_mongo_client.return_value.test_db.goals
    goal_id = "test_goal_1"
    concept_id = "K1-Rekursion"
    new_status = "Aktiv"

    db_service_instance.update_concept_status(goal_id, concept_id, new_status)
    mock_collection.update_one.assert_called_once_with(
        {"_id": goal_id, "path_structure.id": concept_id},
        {"$set": {"path_structure.$.status": new_status}}
    )

def test_update_concept_status_not_found(db_service_instance, mock_mongo_client):
    """Test updating status for a concept not found."""
    mock_collection = mock_mongo_client.return_value.test_db.goals
    mock_collection.update_one.return_value.matched_count = 0 # Simulate no match
    
    goal_id = "test_goal_1"
    concept_id = "NonExistentConcept"
    new_status = "Aktiv"

    db_service_instance.update_concept_status(goal_id, concept_id, new_status)
    # Assert update_one was called, but matched_count indicates no change
    mock_collection.update_one.assert_called_once() 

def test_serialize_object_id():
    """Test serialize_object_id helper function."""
    obj_id = ObjectId()
    data = {"_id": obj_id, "name": "test"}
    serialized_data = serialize_object_id(data)
    assert serialized_data["_id"] == str(obj_id)
    assert isinstance(serialized_data["_id"], str)

def test_deserialize_object_id():
    """Test deserialize_object_id helper function."""
    obj_id_str = str(ObjectId())
    data = {"_id": obj_id_str, "name": "test"}
    deserialized_data = deserialize_object_id(data)
    assert deserialized_data["_id"] == ObjectId(obj_id_str)
    assert isinstance(deserialized_data["_id"], ObjectId)
