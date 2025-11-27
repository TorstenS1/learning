"""
LLM service for interacting with Gemini API.
Handles API calls, response parsing, and simulation mode.
"""
import json
import requests
import openai
from typing import Optional, List, Dict, Any

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
        if self.use_simulation:
            return self._simulate_response(system_prompt, user_prompt)
        else:
            return self._real_api_call(system_prompt, user_prompt, use_grounding, temperature, max_tokens)
    
    def _simulate_response(self, system_prompt: str, user_prompt: str) -> str:
        """
        Generate simulated LLM responses based on agent role.
        
        Args:
            system_prompt: System prompt to determine agent role
            user_prompt: User input
            
        Returns:
            Simulated response text
        """
        print("--- LLM API CALL (SIMULATION) ---")
        print(f"Role (System Prompt Length): {len(system_prompt)} characters")
        print(f"User Prompt: '{user_prompt[:200]}...'")
        print("---------------------------------")
        
        # Determine agent role from system prompt
        if "ARCHITEKT" in system_prompt:
            if "Pfad-Chirurgie" in user_prompt or "Pfad-Chirurgie" in system_prompt:
                return "SIMULATION: ARCHITEKT hat Pfad korrigiert. Neues Konzept: N1: Fundamentale Basis."
            return """SIMULATION: ARCHITEKT hat SMART-Vertrag und Pfadstruktur erstellt.

### LERNZIEL-VERTRAG
Das Ziel wurde standardisiert:
- **S**pezifisch: Implementierung eines KI-Empfehlungssystems
- **M**essbar: Funktionierende Testsuite mit 95% Code-Coverage
- **A**ttraktiv: Praxisrelevantes Projekt
- **R**ealistisch: Mit Python und vorhandenen Bibliotheken
- **T**erminiert: 4 Wochen Lernzeit

### INITIALER LERNPFAD
1. Python/Pandas-Grundlagen (Bloom 2)
2. Einführung in Matrix-Faktorisierung (Bloom 3)
3. Implementierung der Empfehlungslogik (Bloom 5)"""
        
        elif "KURATOR" in system_prompt:
            if "Testfragen" in user_prompt or "Test" in user_prompt:
                return """SIMULATION: KURATOR hat Testfragen generiert.

### TESTFRAGEN

**Frage 1 (Multiple Choice - Bloom 3: Anwenden)**
Welche der folgenden Methoden eignet sich am besten für kollaboratives Filtern?
a) K-Means Clustering
b) Matrix-Faktorisierung ✓
c) Lineare Regression
d) Entscheidungsbäume

**Frage 2 (Freitext - Bloom 4: Analysieren)**
Erklären Sie, warum Matrix-Faktorisierung bei dünn besetzten Matrizen effizienter ist als direkte Ähnlichkeitsberechnungen.

**Frage 3 (Anwendung - Bloom 5: Evaluieren)**
Gegeben ist ein Datensatz mit 10.000 Nutzern und 5.000 Produkten. Bewerten Sie, ob SVD oder ALS die bessere Wahl wäre und begründen Sie Ihre Entscheidung."""
            
            return """SIMULATION: KURATOR hat Material generiert.

### MATERIAL: Einführung in Matrix-Faktorisierung

**Analogie-basierte Erklärung:**
Stellen Sie sich Netflix vor. Die riesige Film-Nutzer-Matrix (Millionen von Nutzern × Tausende von Filmen) ist wie ein gigantisches Puzzle. Matrix-Faktorisierung zerlegt dieses Puzzle in zwei kleinere, handhabbare Teile:

1. **Nutzer-Merkmale-Matrix**: Was mögen Nutzer? (Action, Drama, Sci-Fi)
2. **Film-Merkmale-Matrix**: Welche Eigenschaften haben Filme?

Durch diese Zerlegung können wir verborgene Muster entdecken und Empfehlungen geben, selbst wenn ein Nutzer einen Film noch nicht gesehen hat.

### EXTERN VERFÜGBAR
- [Video: Matrix Factorization Explained](https://youtube.com/watch?v=example)
- [Paper: Collaborative Filtering via Matrix Factorization](https://example.com/paper)"""
        
        elif "TUTOR" in system_prompt:
            if "Lücken-Diagnose" in system_prompt or "Diagnose" in user_prompt:
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
        print(f"--- LLM API CALL (REAL - Provider: {self.provider.upper()}) ---")
        print(f"User Prompt: '{user_prompt[:200]}...'")
        print("--------------------------------------------------")

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
