"""
Database service for Firestore operations.
Provides both real Firestore client and simulator for development.
"""
from typing import Dict, Any, Optional
import json


class FirestoreClientSimulator:
    """
    Simulates Firestore operations for development and testing.
    Stores data in memory without requiring Firebase credentials.
    """
    
    def __init__(self):
        print("Firestore Simulator: Initialized.")
        self.data: Dict[str, Any] = {}
    
    def collection(self, path: str) -> Dict[str, Any]:
        """
        Get or create a collection at the specified path.
        
        Args:
            path: Collection path (e.g., 'goals', 'users')
            
        Returns:
            Dictionary representing the collection
        """
        if path not in self.data:
            self.data[path] = {}
        return self.data[path]
    
    def document(self, collection_path: str, doc_id: str) -> Dict[str, Any]:
        """
        Get a document from a collection.
        
        Args:
            collection_path: Path to the collection
            doc_id: Document identifier
            
        Returns:
            Document data or empty dict if not found
        """
        collection = self.collection(collection_path)
        return collection.get(doc_id, {})
    
    def set(self, collection_path: str, doc_id: str, data: Dict[str, Any], merge: bool = False) -> None:
        """
        Set or update a document in a collection.
        
        Args:
            collection_path: Path to the collection
            doc_id: Document identifier
            data: Data to store
            merge: If True, merge with existing data; if False, replace
        """
        collection = self.collection(collection_path)
        
        if merge and doc_id in collection:
            collection[doc_id].update(data)
        else:
            collection[doc_id] = data
        
        print(f"Firestore Simulator: Document '{doc_id}' in '{collection_path}' updated.")
    
    def get_all(self, collection_path: str) -> Dict[str, Any]:
        """
        Get all documents in a collection.
        
        Args:
            collection_path: Path to the collection
            
        Returns:
            Dictionary of all documents in the collection
        """
        return self.collection(collection_path)
    
    def delete(self, collection_path: str, doc_id: str) -> None:
        """
        Delete a document from a collection.
        
        Args:
            collection_path: Path to the collection
            doc_id: Document identifier
        """
        collection = self.collection(collection_path)
        if doc_id in collection:
            del collection[doc_id]
            print(f"Firestore Simulator: Document '{doc_id}' deleted from '{collection_path}'.")


class FirestoreService:
    """
    Wrapper service for Firestore operations.
    Automatically uses simulator or real client based on configuration.
    """
    
    def __init__(self, use_simulator: bool = True):
        """
        Initialize Firestore service.
        
        Args:
            use_simulator: If True, use simulator; if False, use real Firestore client
        """
        self.use_simulator = use_simulator
        
        if use_simulator:
            self.client = FirestoreClientSimulator()
        else:
            # Real Firestore initialization
            try:
                from google.cloud import firestore
                from firebase_admin import credentials, initialize_app
                from backend.config.settings import FIREBASE_CREDENTIALS_PATH
                
                cred = credentials.Certificate(FIREBASE_CREDENTIALS_PATH)
                initialize_app(cred)
                self.client = firestore.client()
                print("Firestore: Real client initialized.")
            except Exception as e:
                print(f"Firestore: Failed to initialize real client: {e}")
                print("Firestore: Falling back to simulator.")
                self.client = FirestoreClientSimulator()
                self.use_simulator = True
    
    def save_goal(self, goal_id: str, goal_data: Dict[str, Any]) -> None:
        """Save a learning goal to the database."""
        if self.use_simulator:
            self.client.set("goals", goal_id, goal_data)
        else:
            self.client.collection("goals").document(goal_id).set(goal_data)
    
    def get_goal(self, goal_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a learning goal from the database."""
        if self.use_simulator:
            return self.client.document("goals", goal_id)
        else:
            doc = self.client.collection("goals").document(goal_id).get()
            return doc.to_dict() if doc.exists else None
    
    def save_path(self, goal_id: str, path_structure: list) -> None:
        """Save a learning path structure."""
        if self.use_simulator:
            self.client.set(f"goals/{goal_id}/path", "structure", {"concepts": path_structure})
        else:
            self.client.collection("goals").document(goal_id).collection("path").document("structure").set({
                "concepts": path_structure
            })
    
    def update_concept_status(self, goal_id: str, concept_id: str, status: str) -> None:
        """Update the status of a specific concept."""
        if self.use_simulator:
            path_data = self.client.document(f"goals/{goal_id}/path", "structure")
            if path_data and "concepts" in path_data:
                for concept in path_data["concepts"]:
                    if concept.get("id") == concept_id:
                        concept["status"] = status
                self.client.set(f"goals/{goal_id}/path", "structure", path_data, merge=True)
        else:
            # Real Firestore update logic
            pass


# Global instance
db_service: Optional[FirestoreService] = None


def get_db_service(use_simulator: bool = True) -> FirestoreService:
    """
    Get or create the global database service instance.
    
    Args:
        use_simulator: Whether to use the simulator
        
    Returns:
        FirestoreService instance
    """
    global db_service
    if db_service is None:
        db_service = FirestoreService(use_simulator=use_simulator)
    return db_service
