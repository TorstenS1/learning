import json
from datetime import datetime
from typing import Optional, List
from backend.models.state import LogEntry
import os

class LoggingService:
    """
    Service for handling logging operations within the ALIS system.
    It prints log entries to the console and can optionally write them to a file.
    In the future, this will interact with Firestore or another persistence layer.
    """

    def __init__(self, log_file_path: Optional[str] = None):
        self.log_file_path = log_file_path
        self.log_file = None
        if self.log_file_path:
            try:
                # Ensure the directory exists
                os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
                self.log_file = open(log_file_path, 'a', encoding='utf-8')
                print(f"Logging to file: {log_file_path}")
            except IOError as e:
                print(f"Warning: Could not open log file {log_file_path}: {e}")
                self.log_file = None

    def create_log_entry(
        self,
        eventType: str,
        conceptId: Optional[str] = None,
        textContent: Optional[str] = None,
        emotionFeedback: Optional[str] = None,
        testScore: Optional[int] = None,
        kognitiveDiskrepanz: Optional[str] = None,
        groundingSources: Optional[List[str]] = None
    ) -> LogEntry:
        """
        Creates and logs an entry.
        
        Args:
            eventType: Type of event (e.g., 'P5_Chat', 'P1_Zielsetzung').
            conceptId: ID of the concept related to the log entry.
            textContent: Relevant text content.
            emotionFeedback: Detected emotion.
            testScore: Score on a test.
            kognitiveDiskrepanz: Cognitive discrepancy.
            groundingSources: List of URLs for grounding.
            
        Returns:
            A dictionary representing the created log entry.
        """
        timestamp = datetime.now().isoformat()
        log_entry: LogEntry = {
            "timestamp": timestamp,
            "eventType": eventType,
        }
        if conceptId is not None:
            log_entry["conceptId"] = conceptId
        if textContent is not None:
            log_entry["textContent"] = textContent
        if emotionFeedback is not None:
            log_entry["emotionFeedback"] = emotionFeedback
        if testScore is not None:
            log_entry["testScore"] = testScore
        if kognitiveDiskrepanz is not None:
            log_entry["kognitiveDiskrepanz"] = kognitiveDiskrepanz
        if groundingSources is not None:
            log_entry["groundingSources"] = groundingSources
            
        print(f"ALIS Log: {log_entry}")
        
        if self.log_file:
            try:
                self.log_file.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
                self.log_file.flush() # Ensure it's written to disk immediately
            except IOError as e:
                print(f"Warning: Could not write to log file: {e}")

        return log_entry

# Global workflow instance, configured for file logging in the temporary directory
_log_file_path = os.path.join("/home/torsten/.gemini/tmp/f15fe6d1fb2338c1f0733f18f430ec325e6f7292dadf17f61ef851120966e7bf", "alis_log.jsonl")
logging_service = LoggingService(log_file_path=_log_file_path)
