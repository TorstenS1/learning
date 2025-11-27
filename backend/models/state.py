"""
Data models for ALIS system state management.
Defines the TypedDict structures used throughout the application.
"""
from typing import TypedDict, List, Optional


class ALISState(TypedDict):
    """
    Defines the state passed between agents in the LangGraph workflow.
    
    Attributes:
        user_id: Unique identifier for the user
        goal_id: Optional unique identifier for the learning goal (can be derived from `goal` object)
        goal: Optional Goal object containing detailed goal information
        path_structure: List of concept dictionaries representing the learning path
        current_concept: The concept currently being studied
        llm_output: Latest response from the LLM
        user_input: User's message or goal input
        remediation_needed: Flag indicating if gap-filling loop is active
        user_profile: User preferences and learning metrics
    """
    user_id: str
    goal_id: Optional[str]
    goal: Optional['Goal']
    path_structure: List[dict]
    current_concept: dict
    llm_output: str
    user_input: str
    remediation_needed: bool
    user_profile: 'UserProfile'


class ConceptDict(TypedDict, total=False):
    """
    Structure for a single learning concept.
    
    Attributes:
        id: Unique identifier for the concept
        name: Human-readable name
        status: Current status (Offen, Aktiv, Übersprungen, Reaktiviert, Abgeschlossen)
        expertiseSource: Source of expertise marking (P3 Experte, P5.5 Remediation)
        requiredBloomLevel: Bloom's taxonomy level (1-6)
        estimatedTime: Estimated time to complete in minutes
    """
    id: str
    name: str
    status: str
    expertiseSource: Optional[str]
    requiredBloomLevel: Optional[int]
    estimatedTime: Optional[int]


class UserProfile(TypedDict, total=False):
    """
    User learning preferences and metrics.
    
    Attributes:
        stylePreference: Learning style (e.g., 'Analogien-basiert', 'Formal')
        complexityLevel: Preferred complexity (1-5)
        paceWPM: Reading pace in words per minute
        affectiveState: Current emotional state
        errorPatterns: Common error categories
        P2Enabled: Boolean indicating if pre-assessment (P2) is enabled
        P6Enabled: Boolean indicating if post-assessment (P6) is enabled
        lastActiveGoalId: ID of the last active learning goal
    """
    stylePreference: str
    complexityLevel: int
    paceWPM: int
    affectiveState: Optional[str]
    errorPatterns: Optional[List[str]]
    P2Enabled: Optional[bool]
    P6Enabled: Optional[bool]
    lastActiveGoalId: Optional[str]


class Goal(TypedDict, total=False):
    """
    Structure for a learning goal.
    
    Attributes:
        goalId: Unique identifier for the learning goal
        name: Human-readable name of the goal
        fachgebiet: Subject area of the goal
        targetDate: Target completion date
        bloomLevel: Bloom's taxonomy level for the goal
        messMetrik: Measurable metric for goal achievement
        status: Current status of the goal (e.g., 'In Arbeit', 'Abgeschlossen')
    """
    goalId: str
    name: str
    fachgebiet: str
    targetDate: str
    bloomLevel: int
    messMetrik: str
    status: str


class LogEntry(TypedDict, total=False):
    """
    Structure for a detailed log entry, essential for P7 and export.
    
    Attributes:
        timestamp: ISO 8601 formatted timestamp of the event.
        eventType: Type of event (e.g., 'P5_Chat', 'P1_Zielsetzung', 'P3_Skip').
        conceptId: ID of the concept related to the log entry.
        textContent: The relevant text content (e.g., chat message, user input).
        emotionFeedback: Detected emotion (e.g., 'Frustration/Verwirrung').
        testScore: Score on a test (0-100).
        kognitiveDiskrepanz: Indication of cognitive discrepancy.
        groundingSources: List of URLs used for grounding.
    """
    timestamp: str
    eventType: str
    conceptId: Optional[str]
    textContent: Optional[str]
    emotionFeedback: Optional[str]
    testScore: Optional[int]
    kognitiveDiskrepanz: Optional[str]
    groundingSources: Optional[List[str]]

