import os
import sys
from pymongo.errors import ConnectionFailure, PyMongoError

# Add the backend directory to sys.path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from backend.services.db_service import get_db_service
from backend.models.state import UserProfile, Goal, LogEntry # Not directly used, but good for context


def init_db():
    """
    Initializes the MongoDB database by checking/creating collections and indexes.
    """
    print("Attempting to initialize MongoDB...")
    db_service = get_db_service()

    if not db_service.client:
        print("ERROR: MongoDB connection failed. Please ensure MongoDB is running and accessible.")
        return

    try:
        # Define expected collections and their indexes
        collections_and_indexes = {
            "user_profiles": [
                ({"_id": 1}, {"unique": True, "name": "user_id_unique_idx"}),
                ({"lastActiveGoalId": 1}, {"name": "last_active_goal_idx"}) # Optional: if we query by this
            ],
            "goals": [
                ({"_id": 1}, {"unique": True, "name": "goal_id_unique_idx"}),
                ({"userId": 1}, {"name": "user_id_idx"}), # Assuming Goal will store userId
                ({"status": 1}, {"name": "goal_status_idx"})
            ],
            "logs": [
                ({"timestamp": 1}, {"name": "timestamp_idx"}),
                ({"conceptId": 1}, {"name": "concept_id_idx"}),
                ({"eventType": 1}, {"name": "event_type_idx"}),
                ({"userId": 1}, {"name": "log_user_id_idx"}) # Assuming LogEntry will store userId
            ]
        }

        db_name = db_service.db.name
        print(f"Connected to database: '{db_name}'")

        for collection_name, indexes in collections_and_indexes.items():
            collection = db_service._get_collection(collection_name) # Access private method for simplicity in script
            print(f"Checking collection: '{collection_name}'")

            # Ensure collections exist (they are created implicitly on first insert if not present)
            # For robust schema management, we focus on indexes

            for index_keys, index_options in indexes:
                index_name = index_options.get("name", "_".join(index_keys.keys()) + "_idx")
                try:
                    collection.create_index(index_keys, **index_options)
                    print(f"  - Created/Ensured index: '{index_name}' on {list(index_keys.keys())}")
                except PyMongoError as e:
                    print(f"  - WARNING: Could not create index '{index_name}' for '{collection_name}': {e}")
                    # This might happen if an index with the same name but different options already exists

        print("\nMongoDB initialization complete.")

    except ConnectionFailure:
        print("ERROR: MongoDB connection lost during initialization.")
    except PyMongoError as e:
        print(f"ERROR: A MongoDB error occurred during initialization: {e}")
    except Exception as e:
        print(f"ERROR: An unexpected error occurred during database initialization: {e}")
    finally:
        db_service.close_connection()

if __name__ == "__main__":
    init_db()
