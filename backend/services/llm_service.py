"""
LLM service for interacting with Gemini API.
Handles API calls, response parsing, and simulation mode.
"""
import json
import requests
import openai
from typing import Optional, List, Dict, Any
from datetime import datetime
import os

from backend.config.settings import (
    GEMINI_API_KEY, GEMINI_API_URL, DEFAULT_TEMPERATURE, DEFAULT_MAX_TOKENS,
    OPENAI_API_KEY, OPENAI_MODEL_NAME, LLM_PROVIDER
)


class LLMService:
    """
    Service for LLM API interactions.
    Supports both real API calls (Gemini or OpenAI) and simulation mode.
    """
    
    def __init__(self, use_simulation: bool = True):
        """
        Initialize LLM service.
        
        Args:
            use_simulation: If True, use hardcoded responses; if False, call real API
        """
        self.use_simulation = use_simulation
        self.provider = LLM_PROVIDER
        self.client = None
        
        # Setup LLM call logging
        self.llm_log_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'logs', 'llm_calls')
        os.makedirs(self.llm_log_dir, exist_ok=True)
        self.llm_log_file = os.path.join(self.llm_log_dir, f'llm_calls_{datetime.now().strftime("%Y%m%d")}.jsonl')

        if not use_simulation:
            if self.provider == "gemini":
                self.api_key = GEMINI_API_KEY
                self.api_url = GEMINI_API_URL
                if not self.api_key:
                    print("Warning: GEMINI_API_KEY not set. Falling back to simulation mode.")
                    self.use_simulation = True
            elif self.provider == "openai":
                self.api_key = OPENAI_API_KEY
                self.model_name = OPENAI_MODEL_NAME
                if not self.api_key:
                    print("Warning: OPENAI_API_KEY not set. Falling back to simulation mode.")
                    self.use_simulation = True
                else:
                    self.client = openai.OpenAI(api_key=self.api_key)
            else:
                print(f"Warning: Unknown LLM_PROVIDER '{self.provider}'. Falling back to simulation mode.")
                self.use_simulation = True
    
    def _log_llm_call(self, request_data: Dict[str, Any], response_data: Dict[str, Any], error: Optional[str] = None):
        """
        Log LLM call details to both console and file.
        
        Args:
            request_data: Request details (system_prompt, user_prompt, parameters)
            response_data: Response details (text, tokens, etc.)
            error: Error message if call failed
        """
        timestamp = datetime.now().isoformat()
        
        # Create log entry
        log_entry = {
            'timestamp': timestamp,
            'provider': self.provider,
            'simulation': self.use_simulation,
            'request': request_data,
            'response': response_data,
            'error': error
        }
        
        # Console logging (formatted)
        print("\n" + "="*80)
        print(f"🤖 LLM CALL LOG - {timestamp}")
        print("="*80)
        print(f"Provider: {self.provider.upper()} {'(SIMULATION)' if self.use_simulation else '(REAL API)'}")
        print(f"\n📤 REQUEST:")
        print(f"  System Prompt: {request_data.get('system_prompt', '')[:200]}...")
        print(f"  User Prompt: {request_data.get('user_prompt', '')[:200]}...")
        print(f"  Temperature: {request_data.get('temperature', 'N/A')}")
        print(f"  Max Tokens: {request_data.get('max_tokens', 'N/A')}")
        print(f"  Grounding: {request_data.get('use_grounding', False)}")
        
        if error:
            print(f"\n❌ ERROR:")
            print(f"  {error}")
        else:
            print(f"\n📥 RESPONSE:")
            response_text = response_data.get('text', '')
            print(f"  Length: {len(response_text)} characters")
            print(f"  Preview: {response_text[:300]}...")
            if 'tokens_used' in response_data:
                print(f"  Tokens Used: {response_data['tokens_used']}")
        
        print("="*80 + "\n")
        
        # File logging (JSONL format)
        try:
            with open(self.llm_log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
        except Exception as e:
            print(f"Warning: Could not write to LLM log file: {e}")
    
    def call(
        self,
        system_prompt: str,
        user_prompt: str,
        use_grounding: bool = False, # Grounding currently only implemented for Gemini in _real_api_call
        temperature: float = DEFAULT_TEMPERATURE,
        max_tokens: int = DEFAULT_MAX_TOKENS
    ) -> str:
        """
        Make an LLM API call.
        
        Args:
            system_prompt: System/role prompt defining agent behavior
            user_prompt: User's input or task description
            use_grounding: Whether to enable Google Search grounding (provider-dependent)
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens in response
            
        Returns:
            LLM response text
        """
        request_data = {
            'system_prompt': system_prompt,
            'user_prompt': user_prompt,
            'use_grounding': use_grounding,
            'temperature': temperature,
            'max_tokens': max_tokens
        }
        
        try:
            if self.use_simulation:
                response_text = self._simulate_response(system_prompt, user_prompt)
            else:
                response_text = self._real_api_call(system_prompt, user_prompt, use_grounding, temperature, max_tokens)
            
            response_data = {
                'text': response_text,
                'success': True
            }
            
            self._log_llm_call(request_data, response_data)
            return response_text
            
        except Exception as e:
            error_msg = str(e)
            response_data = {
                'text': '',
                'success': False
            }
            self._log_llm_call(request_data, response_data, error=error_msg)
            raise
    
    def _simulate_response(self, system_prompt: str, user_prompt: str) -> str:
        """
        Generate simulated LLM responses based on agent role.
        
        Args:
            system_prompt: System prompt to determine agent role
            user_prompt: User input
            
        Returns:
            Simulated response text
        """
        # Determine agent role from system prompt (check for both English and German)
        if "ARCHITECT" in system_prompt or "ARCHITEKT" in system_prompt:
            if "[ACTION: PERFORM_PATH_SURGERY]" in user_prompt:
                # Simulate path surgery LLM output
                # This should return the new path_structure and current_concept in JSON
                return json.dumps({
                    "path_structure": [
                        {"id": "N1-Fundamentale Basis", "name": "Fundamentale Basis", "status": "Open", "expertiseSource": "P5.5 Remediation", "requiredBloomLevel": 1},
                        {"id": "K1-Grundlagen", "name": "Basiswissen (Reaktiviert)", "status": "Reactivated", "expertiseSource": "P3 Experte", "requiredBloomLevel": 2},
                        {"id": "K2-Kernkonzept", "name": "Kernkonzepte", "status": "Open", "requiredBloomLevel": 3},
                    ],
                    "new_current_concept": {"id": "N1-Fundamentale Basis", "name": "Fundamentale Basis", "status": "Open", "expertiseSource": "P5.5 Remediation", "requiredBloomLevel": 1}
                })
            elif "[ACTION: CREATE_GOAL_PATH]" in user_prompt:
                return json.dumps({
                "goal_contract": {
                    "name": user_prompt,
                    "fachgebiet": "Künstliche Intelligenz",
                    "targetDate": "2025-12-31",
                    "bloomLevel": 3,
                    "messMetrik": "95% Code-Coverage",
                    "status": "In Arbeit"
                },
                "path_structure": [
                    {"id": "K1-Grundlagen", "name": "Python/Pandas-Grundlagen", "status": "Open", "requiredBloomLevel": 2},
                    {"id": "K2-Kernkonzept", "name": "Einführung in Matrix-Faktorisierung", "status": "Open", "requiredBloomLevel": 3},
                    {"id": "K3-Implementierung", "name": "Implementierung der Empfehlungslogik", "status": "Open", "requiredBloomLevel": 5}
                ]
            })
        
        elif "CURATOR" in system_prompt or "KURATOR" in system_prompt:
            if "[ACTION: EVALUATE_TEST]" in user_prompt: # Simulate test evaluation
                import random
                passed = random.choice([True, False])
                score = random.randint(75, 100) if passed else random.randint(30, 65)
                
                feedback = (
                    "Sehr gut! Sie haben das Konzept verstanden und die Fragen korrekt beantwortet." 
                    if passed else 
                    "Sie haben das Konzept noch nicht vollständig durchdrungen. Es gibt Lücken im Verständnis der Kernprinzipien."
                )
                
                recommendation = (
                    "Fahren Sie mit dem nächsten Konzept fort." 
                    if passed else 
                    "Wir empfehlen, das Lernmaterial zu wiederholen oder die Lückenanalyse (P5.5) zu nutzen."
                )
                
                return json.dumps({
                    "score": score,
                    "passed": passed,
                    "feedback": feedback,
                    "recommendation": recommendation,
                    "question_results": [
                        {
                            "id": "q1",
                            "question_text": "Welche der folgenden Methoden eignet sich am besten für kollaboratives Filtern?",
                            "user_answer": "Matrix-Faktorisierung",
                            "correct_answer": "Matrix-Faktorisierung",
                            "is_correct": True,
                            "explanation": "Matrix-Faktorisierung ist eine Standardmethode für kollaboratives Filtern."
                        },
                        {
                            "id": "q2",
                            "question_text": "Erklären Sie, warum Matrix-Faktorisierung bei dünn besetzten Matrizen effizienter ist als direkte Ähnlichkeitsberechnungen.",
                            "user_answer": "Weil sie Dimensionen reduziert.",
                            "correct_answer": "N/A (Freitext)",
                            "is_correct": passed, # Dependent on pass/fail
                            "explanation": "Korrekt, durch die Zerlegung in latente Faktoren wird die Dimensionalität reduziert." if passed else "Nicht ganz. Der Hauptvorteil liegt in der Handhabung latenter Faktoren."
                        },
                        {
                            "id": "q3",
                            "question_text": "Gegeben ist ein Datensatz mit 10.000 Nutzern und 5.000 Produkten. Bewerten Sie, ob SVD oder ALS die bessere Wahl wäre...",
                            "user_answer": "SVD",
                            "correct_answer": "ALS (Alternating Least Squares)",
                            "is_correct": False,
                            "explanation": "Bei explizitem Feedback ist SVD gut, aber bei großen, dünnen Matrizen ist ALS oft skalierbarer."
                        }
                    ]
                })
            elif "[ACTION: GENERATE_TEST]" in user_prompt: # Simulate test generation
                return json.dumps({
                    "test_questions": [
                        {
                            "id": "q1",
                            "question_text": "Welche der folgenden Methoden eignet sich am besten für kollaboratives Filtern?",
                            "type": "multiple_choice",
                            "options": ["K-Means Clustering", "Matrix-Faktorisierung", "Lineare Regression", "Entscheidungsbäume"]
                        },
                        {
                            "id": "q2",
                            "question_text": "Erklären Sie, warum Matrix-Faktorisierung bei dünn besetzten Matrizen effizienter ist als direkte Ähnlichkeitsberechnungen.",
                            "type": "free_text"
                        },
                        {
                            "id": "q3",
                            "question_text": "Gegeben ist ein Datensatz mit 10.000 Nutzern und 5.000 Produkten. Bewerten Sie, ob SVD oder ALS die bessere Wahl wäre und begründen Sie Ihre Entscheidung.",
                            "type": "free_text"
                        }
                    ]
                })
            elif "[ACTION: GENERATE_MATERIAL]" in user_prompt or "Generate learning material" in user_prompt:
                return """SIMULATION: CURATOR has generated material.

### MATERIAL: Introduction to Matrix Factorization

**Analogy-based Explanation:**
Imagine Netflix. The huge movie-user matrix (millions of users × thousands of movies) is like a gigantic puzzle. Matrix factorization breaks this puzzle into two smaller, manageable pieces:

1. **User-Feature Matrix**: What do users like? (Action, Drama, Sci-Fi)
2. **Movie-Feature Matrix**: What properties do movies have?

By breaking it down this way, we can discover hidden patterns and make recommendations, even if a user hasn't seen a movie yet.

### EXTERNAL SOURCES
- [Video: Matrix Factorization Explained](https://youtube.com/watch?v=example)
- [Paper: Collaborative Filtering via Matrix Factorization](https://example.com/paper)"""
            else:
                # Default fallback for CURATOR - return empty test questions
                return json.dumps({"test_questions": []})
        
        elif "ASSESSOR" in system_prompt or "PRÜFER" in system_prompt:
            if "[ACTION: GENERATE_P2_TEST]" in user_prompt:
                return json.dumps({
                    "questions": [
                        {"id": "pk1", "question_text": "Was ist der Unterschied zwischen Supervised und Unsupervised Learning?", "type": "free_text"},
                        {"id": "pk2", "question_text": "Kennen Sie die Bibliothek Pandas?", "type": "multiple_choice", "options": ["Ja, sehr gut", "Ein wenig", "Nein"]},
                        {"id": "pk3", "question_text": "Haben Sie bereits Erfahrung mit Matrix-Faktorisierung?", "type": "multiple_choice", "options": ["Ja", "Nein"]}
                    ]
                })
            elif "[ACTION: EVALUATE_P2_TEST]" in user_prompt:
                # More realistic simulation: check if user input suggests knowledge
                mastered = []
                if 'Ja' in user_prompt: # Simple check on the answers string
                    mastered.append("K1-Grundlagen")
                
                return json.dumps({
                    "mastered_concepts": mastered,
                    "feedback": "Ihre Antworten wurden ausgewertet. Der Lernpfad wird angepasst."
                })

        elif "TUTOR" in system_prompt:
            if "[ACTION: DIAGNOSE_GAP]" in user_prompt:
                return """SIMULATION: TUTOR diagnostiziert Lücke.

Hallo! Ich verstehe, dass das Konzept gerade schwierig erscheint. Das ist völlig normal und passiert jedem beim Lernen. 

Um Ihnen gezielt zu helfen, brauche ich mehr Informationen: **Welches Schlüsselkonzept** fehlt Ihnen genau, um 'Matrix-Faktorisierung' zu verstehen? 

Ist es vielleicht:
- Grundlagen der linearen Algebra?
- Verständnis von Matrizen und Vektoren?
- Oder etwas anderes?

Nennen Sie mir das Fundament, das wackelt, dann können wir es gemeinsam festigen! 💪"""
            
            return """SIMULATION: TUTOR antwortet.

Das ist eine sehr gute Frage! Frustration beim Lernen ist ein Zeichen dafür, dass Sie sich herausfordern – das ist großartig! 🌟

Denken Sie daran: Jeder Fehler bringt Sie näher ans Ziel. Lassen Sie mich Ihnen helfen...

[Hier würde die spezifische Antwort auf Ihre Frage folgen]"""
        
        return "SIMULATION: LLM-Antwort nicht definiert."
    
    def _real_api_call(
        self,
        system_prompt: str,
        user_prompt: str,
        use_grounding: bool,
        temperature: float,
        max_tokens: int
    ) -> str:
        """
        Make a real API call to the configured LLM provider (Gemini or OpenAI).
        
        Args:
            system_prompt: System prompt
            user_prompt: User prompt
            use_grounding: Enable grounding (provider-dependent)
            temperature: Sampling temperature
            max_tokens: Max response tokens
            
        Returns:
            API response text
            
        Raises:
            Exception: If API call fails
        """
        if self.provider == "gemini":
            return self._call_gemini_api(system_prompt, user_prompt, use_grounding, temperature, max_tokens)
        elif self.provider == "openai":
            return self._call_openai_api(system_prompt, user_prompt, temperature, max_tokens)
        else:
            raise Exception(f"Unsupported LLM provider: {self.provider}")

    def _call_gemini_api(
        self,
        system_prompt: str,
        user_prompt: str,
        use_grounding: bool,
        temperature: float,
        max_tokens: int
    ) -> str:
        """
        Make a real API call to Gemini.
        """
        print(f"Endpoint: {self.api_url}")
        print(f"Grounding: {use_grounding}")
        
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": f"{system_prompt}\n\n{user_prompt}"}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            }
        }
        
        if use_grounding:
            payload["tools"] = [{"googleSearch": {}}]
        
        headers = {
            "Content-Type": "application/json",
        }
        
        url = f"{self.api_url}?key={self.api_key}"
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            
            if "candidates" in result and len(result["candidates"]) > 0:
                candidate = result["candidates"][0]
                if "content" in candidate and "parts" in candidate["content"]:
                    parts = candidate["content"]["parts"]
                    if len(parts) > 0 and "text" in parts[0]:
                        return parts[0]["text"]
            
            raise Exception(f"Unexpected Gemini response format: {result}")
        
        except requests.exceptions.RequestException as e:
            print(f"Gemini API call failed: {e}")
            raise Exception(f"LLM API call failed: {str(e)}")

    def _call_openai_api(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_tokens: int
    ) -> str:
        """
        Make a real API call to OpenAI.
        """
        if not self.client:
            raise Exception("OpenAI client not initialized.")

        try:
            chat_completion = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return chat_completion.choices[0].message.content
        except openai.APIError as e:
            print(f"OpenAI API call failed: {e}")
            raise Exception(f"LLM API call failed: {str(e)}")


# Global instance
llm_service: Optional[LLMService] = None


def get_llm_service(use_simulation: bool = True) -> LLMService:
    """
    Get or create the global LLM service instance.
    
    Args:
        use_simulation: Whether to use simulation mode
        
    Returns:
        LLMService instance
    """
    global llm_service
    if llm_service is None:
        llm_service = LLMService(use_simulation=use_simulation)
    return llm_service
