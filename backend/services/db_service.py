from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, PyMongoError
from bson.objectid import ObjectId
from typing import Optional, Dict, Any, List

from backend.config.settings import MONGODB_URI, MONGODB_DB_NAME
from backend.models.state import UserProfile, Goal, LogEntry, ConceptDict


# Helper functions for MongoDB _id conversion
def serialize_object_id(obj: Dict[str, Any]) -> Dict[str, Any]:
    """Converts ObjectId in a dictionary to string for JSON serialization."""
    if "_id" in obj and isinstance(obj["_id"], ObjectId):
        obj["_id"] = str(obj["_id"])
    return obj

def deserialize_object_id(obj: Dict[str, Any]) -> Dict[str, Any]:
    """Converts string _id back to ObjectId for MongoDB queries."""
    if "_id" in obj and isinstance(obj["_id"], str):
        obj["_id"] = ObjectId(obj["_id"])
    return obj


class MongoDBService:
    """
    Service for MongoDB interactions.
    Handles CRUD operations for ALIS data models.
    """

    def __init__(self):
        self.client: Optional[MongoClient] = None
        self.db: Optional[Any] = None
        self._connect()

    def _connect(self):
        """Establishes connection to MongoDB."""
        try:
            self.client = MongoClient(MONGODB_URI)
            # The ismaster command is cheap and does not require auth.
            self.client.admin.command('ismaster') 
            self.db = self.client[MONGODB_DB_NAME]
            print(f"Successfully connected to MongoDB: {MONGODB_URI} (DB: {MONGODB_DB_NAME})")
        except ConnectionFailure as e:
            print(f"ERROR: Could not connect to MongoDB at {MONGODB_URI}. Please ensure MongoDB is running and accessible. {e}")
            self.client = None
            self.db = None
        except Exception as e:
            print(f"An unexpected error occurred during MongoDB connection: {e}")
            self.client = None
            self.db = None

    def _get_collection(self, collection_name: str):
        """Helper to get a collection, reconnecting if necessary."""
        if self.db is None: # Changed from 'if not self.db:'
            print("MongoDB connection lost or not established, attempting to reconnect...")
            self._connect()
            if self.db is None: # Changed from 'if not self.db:'
                raise ConnectionFailure("MongoDB connection not established after reconnect attempt.")
        return self.db[collection_name]

    def save_user_profile(self, user_id: str, profile: UserProfile) -> None:
        """Saves or updates a user profile."""
        collection = self._get_collection("user_profiles")
        try:
            profile_data = profile.copy()
            # Ensure _id is handled if present, typically user_id is natural _id
            profile_data["_id"] = user_id
            collection.replace_one({"_id": user_id}, profile_data, upsert=True)
            print(f"UserProfile for {user_id} saved/updated.")
        except PyMongoError as e:
            print(f"Error saving UserProfile for {user_id}: {e}")
            raise

    def get_user_profile(self, user_id: str) -> Optional[UserProfile]:
        """Retrieves a user profile."""
        collection = self._get_collection("user_profiles")
        try:
            profile = collection.find_one({"_id": user_id})
            if profile:
                return UserProfile(**serialize_object_id(profile))
            return None
        except PyMongoError as e:
            print(f"Error retrieving UserProfile for {user_id}: {e}")
            raise

    def save_goal(self, goal_id: str, goal: Goal) -> None:
        """Saves or updates a learning goal."""
        collection = self._get_collection("goals")
        try:
            goal_data = goal.copy()
            goal_data["_id"] = goal_id
            collection.replace_one({"_id": goal_id}, goal_data, upsert=True)
            print(f"Goal {goal_id} saved/updated.")
        except PyMongoError as e:
            print(f"Error saving Goal {goal_id}: {e}")
            raise

    def get_goal(self, goal_id: str) -> Optional[Goal]:
        """Retrieves a learning goal."""
        collection = self._get_collection("goals")
        try:
            goal = collection.find_one({"_id": goal_id})
            if goal:
                return Goal(**serialize_object_id(goal))
            return None
        except PyMongoError as e:
            print(f"Error retrieving Goal {goal_id}: {e}")
            raise

    def save_log_entry(self, log_entry: LogEntry) -> None:
        """Saves a log entry."""
        collection = self._get_collection("logs")
        try:
            # MongoDB will generate an _id if not provided
            collection.insert_one(log_entry.copy())
            print(f"Log entry saved: {log_entry.get('eventType')}")
        except PyMongoError as e:
            print(f"Error saving LogEntry: {e}")
            raise

    def update_concept_status(self, goal_id: str, concept_id: str, new_status: str) -> None:
        """
        Updates the status of a specific concept within a goal's path_structure.
        This assumes path_structure is part of the Goal document.
        """
        collection = self._get_collection("goals")
        try:
            result = collection.update_one(
                {"_id": goal_id, "path_structure.id": concept_id},
                {"$set": {"path_structure.$.status": new_status}}
            )
            if result.matched_count == 0:
                print(f"Warning: Concept {concept_id} not found in Goal {goal_id}'s path_structure for status update.")
            else:
                print(f"Concept {concept_id} status updated to {new_status} in Goal {goal_id}.")
        except PyMongoError as e:
            print(f"Error updating concept status for {concept_id} in Goal {goal_id}: {e}")
            raise

    def close_connection(self):
        """Closes the MongoDB connection."""
        if self.client:
            self.client.close()
            print("MongoDB connection closed.")


# Global instance for easy access
db_service = MongoDBService()


def get_db_service() -> MongoDBService:
    """Returns the global MongoDBService instance."""
    return db_service
