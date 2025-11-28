"""
Session management for ALIS system.
Allows users to save and restore their learning progress.
"""
from datetime import datetime
from typing import Dict, Any, Optional
from backend.services.db_service import get_db_service


class SessionManager:
    """
    Manages user learning sessions in MongoDB.
    """
    
    def __init__(self):
        self.db = get_db_service()
    
    def save_session(self, user_id: str, session_data: Dict[str, Any], session_name: Optional[str] = None) -> str:
        """
        Save current learning session to database.
        
        Args:
            user_id: User identifier
            session_data: Current application state
            session_name: Optional custom name for the session
            
        Returns:
            Session ID
        """
        # Use custom name or derive from goal
        if not session_name:
            session_name = session_data.get('goalName') or session_data.get('goalId', 'Unnamed Session')
        
        session = {
            'user_id': user_id,
            'session_name': session_name,
            'timestamp': datetime.utcnow().isoformat(),
            'phase': session_data.get('phase'),
            'goal_id': session_data.get('goalId'),
            'goal_name': session_data.get('goalName', session_name),
            'path_structure': session_data.get('pathStructure', []),
            'current_concept': session_data.get('currentConcept'),
            'llm_output': session_data.get('llmOutput', ''),
            'tutor_chat': session_data.get('tutorChat', []),
            'test_evaluation_result': session_data.get('testEvaluationResult'),
            'parsed_test_questions': session_data.get('parsedTestQuestions', []),
            'user_test_answers': session_data.get('userTestAnswers', {}),
            'remediation_needed': session_data.get('remediationNeeded', False),
            'language': session_data.get('language', 'de')
        }
        
        # Store in MongoDB
        collection = self.db.db['sessions']
        
        # Update existing session or create new one
        result = collection.update_one(
            {'user_id': user_id, 'goal_id': session_data.get('goalId')},
            {'$set': session},
            upsert=True
        )
        
        return str(result.upserted_id) if result.upserted_id else 'updated'
    
    def load_session(self, user_id: str, goal_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Load most recent session for user.
        
        Args:
            user_id: User identifier
            goal_id: Optional specific goal ID to load
            
        Returns:
            Session data or None if not found
        """
        collection = self.db.db['sessions']
        
        if goal_id:
            # Load specific goal session
            session = collection.find_one({'user_id': user_id, 'goal_id': goal_id})
        else:
            # Load most recent session
            session = collection.find_one(
                {'user_id': user_id},
                sort=[('timestamp', -1)]
            )
        
        if session:
            # Remove MongoDB _id field
            session.pop('_id', None)
            return session
        
        return None
    
    def list_sessions(self, user_id: str) -> list:
        """
        List all sessions for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            List of session summaries
        """
        collection = self.db.db['sessions']
        sessions = collection.find({'user_id': user_id}).sort('timestamp', -1)
        
        result = []
        for session in sessions:
            result.append({
                'goal_id': session.get('goal_id'),
                'session_name': session.get('session_name', 'Unnamed Session'),
                'goal_name': session.get('goal_name', 'Unknown Goal'),
                'timestamp': session.get('timestamp'),
                'phase': session.get('phase'),
                'current_concept': (session.get('current_concept') or {}).get('name', 'Unknown')
            })
        
        return result
    
    def delete_session(self, user_id: str, goal_id: str) -> bool:
        """
        Delete a specific session.
        
        Args:
            user_id: User identifier
            goal_id: Goal identifier
            
        Returns:
            True if deleted, False otherwise
        """
        collection = self.db.db['sessions']
        result = collection.delete_one({'user_id': user_id, 'goal_id': goal_id})
        return result.deleted_count > 0


# Singleton instance
_session_manager = None

def get_session_manager() -> SessionManager:
    """Get singleton SessionManager instance."""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager
