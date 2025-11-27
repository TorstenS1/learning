# ALIS (Adaptive Lern-App) - Gesamtspezifikation und Implementierungsplan

Dieses Dokument konsolidiert die Architektur, den adaptiven Zyklus, die LLM-Rollen und einen detaillierten, iterativen Implementierungsplan.

## 1. Systemarchitektur und Datenmodell

Das ALIS-System basiert auf einer hybriden Architektur: Google Gemini LLM (als intelligenter Motor) und Firebase/Firestore (als persistente Datenebene).

### 1.1 Das LLM-Rollenmodell (Intelligente Schicht)

Das LLM agiert in drei spezialisierten Rollen, gesteuert durch spezifische Systemanweisungen (Prompts):

| Rolle     | Primäre Aufgabe                                                                      | Phasen        | Persona                               |
| :-------- | :----------------------------------------------------------------------------------- | :------------ | :------------------------------------ |
| Architekt | Ziel- und Pfadplanung, Standardisierung (SMART/Bloom), Dynamische Pfadkorrektur.      | P1, P3, P5.5  | Analytisch, strukturierter Berater.   |
| Kurator   | Content-Generierung, Faktenprüfung (Grounding), Multimedia-Kuration, Test-Generierung. | P4, P6        | Objektiver, fokussierter Fachautor.   |
| Tutor     | Affektive Steuerung (Frustration), Ad-hoc-Hilfe, Fehler-Neubewertung, Diagnose bei Lücken. | P5, P5.5, P7  | Einfühlsamer, geduldiger Mentor (Growth Mindset). |

### 1.2 Firestore Datenstruktur (Persistente Schicht)

Alle Daten werden im privaten Benutzerbereich von Firestore gespeichert (`/artifacts/{appId}/users/{userId}/...`), um die Personalisierung und Dokumentation zu gewährleisten.

| Dokument                               | Zweck                                               | Schlüsselmetriken für Adaptivität                                       |
| :------------------------------------- | :-------------------------------------------------- | :---------------------------------------------------------------------- |
| 1. Lernziel (`/goals/{goalId}`)          | Der SMART/Bloom-Vertrag.                            | `name`, `bloomLevel`, `targetScore`, `status`                             |
| 2. Lernpfad (`/goals/{goalId}/path/structure`) | Die Gliederung.                                     | Array von `{id, name, status, estimatedTime, expertiseSource}`          |
| 3. Nutzerprofil (`/config/profile`)      | Aggregierte Lernmetriken.                           | `paceWPM`, `stylePreference`, `complexityLevel`, `P2Enabled`, `P6Enabled` |
| 4. Lernprotokolle (`/logs/{logId}`)      | Vollständiges, chronologisches Log (für Review/Export). | `timestamp`, `conceptId`, `emotionFeedback`, `testScore`, `kognitiveDiskrepanz` |

## 2. Der Adaptive Lernzyklus (P1 bis P7)

Der Prozess ist modular. Phasen P2 und P6, sowie der Experten-Review (in P3), sind optional/überspringbar.

| Phase | Bezeichnung                 | Funktionalität und Optionalität                                                                                                 |
| :---- | :-------------------------- | :------------------------------------------------------------------------------------------------------------------------------ |
| P1    | SMART-Ziel-Kontrakt         | MANDATORY. Architekt führt Verfeinerung zu messbarem Ziel durch.                                                                |
| P2    | Vorwissenstest              | OPTIONAL. Kurator generiert Test. Bei Erfolg: Konzepte werden auf `Beherrscht` gesetzt.                                         |
| P3    | Pfad-Erstellung & Experten-Review | MANDATORY. Architekt generiert Gliederung. Nutzer kann hier ganze Konzepte als `Bekannt` markieren und überspringen (Abgeleitete Expertise). |
| P4    | Material- und Kuratierung   | MANDATORY. Kurator generiert stil- und niveau-angepasstes Material (mit Grounding) und kuratiert Multimedia.                  |
| P5    | Lernphase                   | MANDATORY. Kernkonsum. Tutor bietet Chat-Hilfe. Enthält den Button "Fundament fehlt".                                          |
| P5.5  | Dynamische Remediation      | KORREKTUR-LOOP. Tutor diagnostiziert Lücke. Architekt fügt neues, notwendiges Fundament-Kapitel an erster Stelle in den Pfad ein. |
| P6    | Verständnisprüfung          | OPTIONAL. Kurator generiert Mastery-Test (an Bloom-Niveau angepasst).                                                           |
| P7    | Anpassung/Motivations-Loop  | AUTOMATISCH. Tutor verarbeitet Frustration/Score-Feedback und passt Stil/Pfad an. Abschluss mit Follow-up Learnings.          |

## 3. Detaillierter Implementierungsplan (Iterative Schritte)

Die Empfehlung basiert auf einer agilen Entwicklung mit React/Tailwind/Firebase, um schnell einen Mehrwert zu liefern.

### Phase 1: MVP (Core Generative Loop & Persistenz)

| Komponente | Implementierung                                                                                                               | LLM-Rollen-Fokus       |
| :--------- | :---------------------------------------------------------------------------------------------------------------------------- | :--------------------- |
| Setup      | Firebase-Initialisierung, anonyme Auth, zentrale LLM-API-Service-Funktion.                                                     |                        |
| P1/P3 Kern | Architekt-Service aufrufen. Speicherung des Lernziel-Vertrags und der Lernpfad-Struktur. UI zur Anzeige der Gliederung und des Experten-Review-Skips. | Architekt              |
| P4/P5 Basis| Kurator-Service aufrufen (reiner Text, ohne Grounding/Vetting). UI zur Anzeige des Lernmaterials und des Fortschritts.            | Kurator                |
| P6 Basis   | Einfache, obligatorische Verständnisprüfung (3x Multiple Choice). Speicherung des Scores in Lernprotokolle.                  | Kurator                |
| P7 Basis   | Einfache Logik: Bei 80%+ Score -> nächstes Konzept. Bei Misserfolg -> Wiederholung.                                            | Tutor (Basis-Feedback) |

### Phase 2: Adaptive Intelligenz und Qualität

| Komponente | Implementierung | LLM-Rollen-Fokus |
| :--- | :--- | :--- |
| Optionalität | Implementierung der Umschalter für P2/P6 im Nutzerprofil. Steuerung der Sichtbarkeit der entsprechenden UI-Elemente. | Architekt, Kurator |
| P2 Vorwissen | Implementierung des Vorwissenstests (P2) und Logik zur Markierung der Kapitel als `Beherrscht`. | Kurator |
| P4 Qualität | Integration der Google Search Grounding (im `callLLM` Service). Implementierung des Vetting-Filters für externe Links (Quellen-Reputation, Aktualität). | Kurator |
| P5/P7 Adaptivität | Tracking der `paceWPM` und `stylePreference`. Übergabe dieser Metriken an den Kurator zur Personalisierung des generierten Materials. | Kurator, Tutor |

### Phase 3: Mentoring, Remediation und Dokumentation (Polishing)

| Komponente | Implementierung | LLM-Rollen-Fokus |
| :--- | :--- | :--- |
| P5.5 Remediation | Implementierung des Buttons "Fundament fehlt". Auslösung des Architekten-Service zur Pfad-Chirurgie und Neuberechnung der Gliederung. | Architekt, Tutor |
| Tutor (Chat) | Vollständige Implementierung der Tutor-Persona (Rolle 3). Affektive Analyse und Einsatz der "Growth Mindset"-Sprache (Fehler-Neubewertung). | Tutor |
| P7 Dokumentation | Aufbau der Lernprotokolle-UI. Export-Funktion (PDF/Markdown) der `Goal Summary` (Score, Zeit, Abgeleitete Expertise). | Architekt |
| P7 Follow-up | Am Ende eines Ziels: LLM-generierte drei konkrete Empfehlungen (Vertiefung, Anwendung, Nächste Stufe) basierend auf den gesammelten Lücken und Stärken. | Architekt |

## 4. Metriken und Wiederverwendung (Zusammenfassung)

Die gesammelten Daten treiben die Adaptivität voran und werden im Nutzerprofil aggregiert:

| Metrik               | Datenerfassung                                         | Wiederverwendung durch LLM                                                                                           |
| :------------------- | :----------------------------------------------------- | :------------------------------------------------------------------------------------------------------------------- |
| Lernstil             | Tracking angeklickter Material-Typen, explizites Feedback. | Kurator (P4): Priorisierung von Analogien, Text oder visuellen Erklärungen in der Generierung.                     |
| Lerngeschw. (Pace)   | Zeit / Wortanzahl des Kapitels (`paceWPM`).               | Architekt (P3): Präzisere Schätzung der Gesamtzeit des Lernpfades und Anpassung der Textlänge (Chunking).            |
| Kognitive Diskr.     | Vergleich von Selbstvertrauen (Nutzer) vs. Test-Score (P6). | Kurator (P6): Generierung von kritischen Prüfungsfragen, die gezielt falsche Annahmen korrigieren.                   |
| Abgeleitete Expertise | Manuelle Skips (P3) oder erfolgreicher Pre-Test (P2).      | Kurator (P4): Annahme von 100% Fundament-Wissen im übersprungenen Bereich. Wird bei P5.5 Lücke sofort revidiert. |

# Technische Spezifikation ALIS (Deep Dive Masterplan)

Dieses Dokument definiert die granularen Workflows, LLM-Schnittstellen und Datenstrukturen für das Adaptive Lern-App-System (ALIS).

## 1. Detaillierte Datenstrukturen (Firestore-Schema)

Alle Daten werden unter `/artifacts/{appId}/users/{userId}/...` gespeichert.

### 1.1 `config/profile` (Nutzerprofil)

Enthält aggregierte und persistente Lernpräferenzen.

```json
{
  "userId": "unique-user-id-string",
  "stylePreference": "Analogien-basiert", // Aus P7 abgeleitet
  "complexityLevel": "Mittel", // Aus P7 abgeleitet
  "paceWPM": 180, // Wörter pro Minute, dynamisch aus P5 berechnet
  "P2Enabled": true, // Boolean: Vorwissenstest aktiv?
  "P6Enabled": true, // Boolean: Verständnisprüfung aktiv?
  "lastActiveGoalId": "G-20251127-12345"
}
```

### 1.2 `goals/{goalId}` (Lernziel-Vertrag)

Der von Architekt (P1) erstellte SMART-Vertrag.

```json
{
  "goalId": "G-20251127-12345",
  "name": "Multi-Agenten-Systeme in der Logistik implementieren",
  "fachgebiet": "Künstliche Intelligenz",
  "targetDate": "2026-03-01",
  "bloomLevel": 5, // 5: Evaluieren
  "messMetrik": "90% korrekte Bewertung von 5 Fallstudien",
  "status": "In Arbeit" // In Arbeit, Abgeschlossen, Abgebrochen
}
```

### 1.3 `goals/{goalId}/path/structure` (Lernpfad-Struktur)

Die sequenzielle Gliederung, dynamisch änderbar (durch P5.5).

```json
[
  {
    "id": "K1-Rekursion",
    "name": "Grundlagen der Rekursion (Eingefügte Lücke)",
    "status": "Offen", // Offen, Beherrscht, Übersprungen, Reaktiviert (durch P5.5)
    "estimatedTime": 25, // Minuten, aus P3/P7 berechnet
    "expertiseSource": "P5.5 Remediation", // P2 Vorwissen, P3 Experte, P5.5 Remediation
    "requiredBloomLevel": 3 // Das notwendige Bloom-Niveau für dieses Konzept
  },
  {
    "id": "K2-Agentenarchitektur",
    "name": "Agentenarchitekturen (Sense-Plan-Act)",
    "status": "Aktiv",
    "estimatedTime": 45,
    "expertiseSource": null,
    "requiredBloomLevel": 4
  }
  // ... weitere Konzepte
]
```

### 1.4 `logs/{logId}` (Lernprotokolle)

Detailliertes Log jeder Interaktion, essenziell für P7 und den Export.

```json
{
  "timestamp": "2025-11-27T10:00:00Z",
  "eventType": "P5_Chat", // P1_Zielsetzung, P3_Skip, P4_Material, P5_Chat, P5.5_Lücke, P6_Test, P7_Feedback
  "conceptId": "K2-Agentenarchitektur",
  "textContent": "Da Sie nach einem einfacheren Beispiel fragten, hier die Analogie...",
  "emotionFeedback": "Frustration/Verwirrung", // Vom Tutor abgeleitet
  "testScore": null,
  "kognitiveDiskrepanz": null,
  "groundingSources": ["URL1", "URL2"]
}
```

## 2. Die LLM-Agenten und System Prompts

Die folgenden Prompts werden als `systemInstruction` in den Gemini API-Aufruf eingebettet.

### 2.1 Rolle 1: Der Architekt (P1, P3, P5.5)

Aufgabe: Strukturierung und Pfadverwaltung.

**System Prompt: ARCHITEKT**

Du bist der **Architekt** im ALIS-System. Deine Aufgabe ist es, die Lernabsicht des Nutzers zu strukturieren und den Lernpfad dynamisch zu verwalten.

**Anweisungen:**

1.  **SMART-Standardisierung (P1):** Verhandle das Ziel, bis es messbar ist. Extrahiere `name`, `fachgebiet`, `targetDate`, `bloomLevel`, `messMetrik`.
2.  **Pfad-Generierung (P3):** Erstelle eine Gliederung (5-10 Konzepte) in logischer Sequenz.
3.  **Experten-Review (P3):** Präsentiere die Gliederung im Format der finalen Ausgabe. Füge `estimatedTime` und `requiredBloomLevel` für jedes Konzept hinzu.
4.  **Dynamische Korrektur (P5.5):** Wenn vom Tutor eine Lücke diagnostiziert wird, führe eine "Pfad-Chirurgie" durch:
    *   Definiere das fehlende Konzept N1.
    *   Füge N1 mit `status: Offen` und `expertiseSource: P5.5 Remediation` an die **Spitze** des Lernpfads.
    *   Setze den Status des ursprünglich übersprungenen Konzepts (falls relevant) auf `Reaktiviert`.
5.  **Output-Format:** Liefere das Ergebnis stets im folgenden Markdown-Format zurück.

### 2.2 Rolle 2: Der Kurator (P4, P6)

Aufgabe: Generierung von Material und Tests, Faktenprüfung.

**System Prompt: KURATOR**

Du bist der **Kurator** im ALIS-System. Deine Aufgabe ist die Generierung von maßgeschneidertem Lernmaterial und validen Tests.

**Anweisungen:**

1.  **Kontext-Einbeziehung:** Nutze die Metriken aus dem `Nutzerprofil` (`stylePreference`, `complexityLevel`, `paceWPM`).
2.  **Inhaltsgenerierung (P4):** Generiere den Text. Der Stil muss zur Präferenz passen (z.B. analogie-basiert). Die Textlänge sollte `paceWPM` berücksichtigen.
3.  **Grounding:** Führe **Google Search** durch, um alle Fakten zu untermauern und die Quellen (`groundingSources`) anzugeben.
4.  **Test-Generierung (P6):** Generiere 3-5 Testfragen (MC, Freitext, etc.), deren Frageniveau dem `bloomLevel` des Konzepts entspricht.
5.  **Output-Format:** Liefere das Ergebnis stets im folgenden Markdown-Format zurück.

### 2.3 Rolle 3: Der Tutor (P5, P5.5, P7)

Aufgabe: Motivation, Diagnose, Ad-hoc-Hilfe.

**System Prompt: TUTOR**

Du bist der **Tutor** im ALIS-System. Deine Priorität liegt in der **affektiven Steuerung** und der individuellen Unterstützung des Nutzers.

**Anweisungen:**

1.  **Affektive Analyse (P7):** Bewerte jeden Nutzereintrag auf emotionale Indikatoren (Frustration, Verwirrung, Freude) und speichere dies als `emotionFeedback`.
2.  **Ad-hoc-Hilfe (P5):** Reagiere auf Fragen, indem du die im `Lernprotokoll` gespeicherten Informationen zum Konzept nutzt.
3.  **Lücken-Diagnose (P5.5):** Wenn der Nutzer den Indikator **'Fundament fehlt'** auslöst:
    *   Wechsle in den Diagnosemodus.
    *   Frage den Nutzer: "**Welches Schlüsselkonzept** fehlt Ihnen genau?"
    *   Sobald das Konzept identifiziert ist, **delegiere die Aufgabe, das neue Kapitel zu erstellen, an den Architekten.**
4.  **Output-Format:** Dein Output ist **immer** ein natürlicher, konversationeller Chat-Dialog.

## 3. Detaillierter Workflow mit Entscheidungspunkten

Der Prozess ist ein dynamischer Loop, der auf Triggern basiert.

### 3.1 P3: Pfad-Erstellung & Experten-Review

*   **Trigger:** Abschluss der P1-Zielverhandlung.
*   **LLM-Rolle:** Architekt.
*   **Entscheidungspunkt: Nutzer-Input (Manuelle Skips):** Der Architekt generiert die Gliederung (Pfad). Das System präsentiert dem Nutzer die Gliederung.
    *   **IF** Konzept von Nutzer als 'Bekannt' markiert: Setze `status` auf `Übersprungen` und `expertiseSource` auf `P3 Experte` in der Datenbank.
    *   **ELSE IF** Konzept durch P2 auf `Beherrscht`: Setze `status` auf `Beherrscht`.
    *   **ELSE:** Setze `status` auf `Offen`.

### 3.2 P5.5: Dynamische Remediation (Der Lücken-Loop)

*   **Trigger:** Nutzer klickt den Button "Fundament fehlt / Lücke melden" während P5.
*   **LLM-Rollen:** Tutor (Diagnose) -> Architekt (Korrektur).
*   **Workflow:**
    1.  Tutor führt die Lücken-Diagnose durch (Konzept-Name N1 identifizieren).
    2.  Tutor delegiert an den Architekten.
    3.  **Entscheidungspunkt (Architekt-Logik):**
        *   Architekt prüft, ob N1 bereits existiert und übersprungen wurde.
        *   **IF** N1 ist übersprungen: Setze N1 auf `status: Reaktiviert`.
        *   **ELSE:** Erstelle N1 neu mit `status: Offen`.
    4.  **Pfad-Update:** Setze N1 an die erste Position im Lernpfad mit `status: Offen`.
    5.  Nächstes Konzept wird N1 (P4 startet).

### 3.3 P6/P7: Verständnisprüfung und Adaption

*   **Trigger:** Abschluss des Materials (P4/P5) und optionaler Test (P6).
*   **LLM-Rollen:** Kurator (Test), Tutor (Feedback/Adaption).
*   **Entscheidungspunkt (Automatisierter Fortschritt):**
    *   **IF** P6 deaktiviert ODER Test-Score >= `targetScore`:
        *   Setze `status` des aktuellen Konzepts auf `Beherrscht`.
        *   Gehe zum nächsten Konzept mit `status: Offen/Aktiv`.
    *   **ELSE (Test nicht bestanden):**
        *   Tutor analysiert die falschen Antworten (Fehler-Kategorisierung).
        *   **Entscheidungspunkt (Remediation):** Tutor entscheidet:
            *   **IF** Fehler sind leicht/oberflächlich: Generiere neues, gezieltes Material (P4) zum gleichen Konzept (z.B. nur ein Anwendungsbeispiel).
            *   **ELSE IF** Fehler sind fundamental: Starte P5.5 Lücken-Diagnose (Das Problem liegt nicht hier, sondern davor).

Dieses Framework stellt sicher, dass das System reaktionsschnell, dokumentiert und vollständig adaptiv auf die individuellen Bedürfnisse und Fehleinschätzungen des Nutzers reagiert.
