"""
Language-specific instructions for ALIS agents.
These will be appended to the system prompts based on the user's language preference.
"""

LANGUAGE_INSTRUCTIONS = {
    'de': """

**WICHTIG - SPRACHANWEISUNG:**
- Antworte IMMER auf Deutsch.
- Alle Erklärungen, Feedback und Materialien müssen in deutscher Sprache verfasst sein.
- JSON-Schlüssel bleiben auf Englisch, aber alle Textwerte müssen auf Deutsch sein.
""",
    
    'en': """

**IMPORTANT - LANGUAGE INSTRUCTION:**
- Always respond in English.
- All explanations, feedback, and materials must be written in English.
- JSON keys remain in English, and all text values must be in English.
"""
}

def get_prompt_with_language(base_prompt: str, language: str = 'de') -> str:
    """
    Append language-specific instructions to a base prompt.
    
    Args:
        base_prompt: The base system prompt
        language: Language code ('de' or 'en')
        
    Returns:
        Complete prompt with language instructions
    """
    lang_instruction = LANGUAGE_INSTRUCTIONS.get(language, LANGUAGE_INSTRUCTIONS['de'])
    return base_prompt + lang_instruction
