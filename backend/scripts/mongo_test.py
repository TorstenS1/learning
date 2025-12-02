import os
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from dotenv import load_dotenv
from bson.objectid import ObjectId

# Load environment variables from .env file
# Assumes the script is run from the root of the 'backend' directory
# or that the .env file is in a parent directory.
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
load_dotenv(dotenv_path=dotenv_path)

def test_mongodb_connection():
    """
    Connects to MongoDB and performs basic CRUD operations to test access.
    """
    # 1. Get Connection String from Environment Variable
    mongo_uri = os.getenv("MONGO_URI")
    if not mongo_uri:
        print("❌ Error: MONGO_URI environment variable not set.")
        print("Please create a .env file in the project root with MONGO_URI='your_connection_string'")
        return

    print(f"Connecting to MongoDB at '{mongo_uri[:20]}...'")

    # 2. Create a new client and connect to the server
    client = MongoClient(mongo_uri)

    try:
        # The ismaster command is cheap and does not require auth.
        client.admin.command('ismaster')
        print("✅ MongoDB connection successful.")
    except ConnectionFailure as e:
        print(f"❌ MongoDB connection failed: {e}")
        return

    try:
        # 3. Define database and collection
        db = client.alis_test_db
        collection = db.test_collection
        print(f"Using database '{db.name}' and collection '{collection.name}'")

        # 4. CREATE (Insert a document)
        print("\n--- 1. CREATE ---")
        test_doc = {"name": "Test User", "role": "Tester", "status": "active"}
        result = collection.insert_one(test_doc)
        doc_id = result.inserted_id
        print(f"Inserted document with ID: {doc_id}")
        assert isinstance(doc_id, ObjectId)

        # 5. READ (Find the document)
        print("\n--- 2. READ ---")
        retrieved_doc = collection.find_one({"_id": doc_id})
        print(f"Retrieved document: {retrieved_doc}")
        assert retrieved_doc is not None
        assert retrieved_doc['name'] == "Test User"

        # 6. UPDATE (Modify the document)
        print("\n--- 3. UPDATE ---")
        update_result = collection.update_one(
            {"_id": doc_id},
            {"$set": {"status": "completed"}}
        )
        print(f"Matched {update_result.matched_count} document, modified {update_result.modified_count}.")
        updated_doc = collection.find_one({"_id": doc_id})
        print(f"Updated document: {updated_doc}")
        assert updated_doc['status'] == "completed"

        # 7. DELETE (Remove the document)
        print("\n--- 4. DELETE ---")
        delete_result = collection.delete_one({"_id": doc_id})
        print(f"Deleted {delete_result.deleted_count} document.")
        deleted_doc = collection.find_one({"_id": doc_id})
        assert deleted_doc is None
        print("Document successfully deleted.")

        print("\n✅ All CRUD operations completed successfully!")

    except Exception as e:
        print(f"❌ An error occurred during database operations: {e}")
    finally:
        # 8. Clean up and close the connection
        print("\nCleaning up test collection...")
        db.drop_collection('test_collection')
        client.close()
        print("Connection closed.")

if __name__ == "__main__":
    test_mongodb_connection()
