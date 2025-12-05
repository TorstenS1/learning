import os
import sys
import pymongo
from pymongo.errors import ConnectionFailure, ConfigurationError

def test_mongo_connection(uri):
    print(f"Testing MongoDB connection...")
    # Mask URI for security in logs
    masked_uri = uri.split('@')[-1] if '@' in uri else '***'
    print(f"Target: ...@{masked_uri}")

    try:
        # Set a short timeout (5s) to fail fast
        client = pymongo.MongoClient(uri, serverSelectionTimeoutMS=5000)
        
        # The ismaster command is cheap and does not require auth.
        client.admin.command('ismaster')
        
        print("✅ Successfully connected to MongoDB!")
        return True
    except ConnectionFailure as e:
        print(f"❌ Connection failed: {e}")
        return False
    except ConfigurationError as e:
        print(f"❌ Configuration error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    MONGO_URI="mongodb+srv://alis_app_user:alis_app_user@cluster0.n5e9osz.mongodb.net/?appName=Cluster0"
    uri = "mongodb+srv://alis_app_user:alis_app_user@cluster0.n5e9osz.mongodb.net/?appName=Cluster0" # os.environ.get("MONGO_URI")

    if not uri:
        print("❌ MONGO_URI environment variable not set")
        sys.exit(1)
    
    if test_mongo_connection(uri):
        sys.exit(0)
    else:
        sys.exit(1)
