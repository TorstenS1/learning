export const de = {
    // P1: Goal Setting
    p1: {
        title: "ALIS: Ziel-Kontrakt (P1)",
        description: "Definieren Sie Ihr Lernziel. Der **Architekt** standardisiert es in einen messbaren **SMART-Vertrag**.",
        placeholder: "Beispiel: Ich möchte Multi-Agenten-Systeme in der Logistik implementieren.",
        buttonSubmit: "SMART-Vertrag erstellen",
        buttonSubmitting: "Ziel wird verhandelt...",
        currentMessage: "Aktuelle LLM-Nachricht:"
    },

    // P2: Prior Knowledge
    p2: {
        choiceTitle: "Vorwissen prüfen? (P2)",
        choiceDescription: "Möchten Sie einen kurzen Test machen, um bereits bekannte Konzepte automatisch zu überspringen?",
        choiceYes: "Ja, Vorwissen testen",
        choiceNo: "Nein, direkt zum Pfad",
        testTitle: "Vorwissenstest (P2)",
        testDescription: "Bitte beantworten Sie die folgenden Fragen, damit wir Ihren Lernpfad anpassen können.",
        yourAnswer: "Ihre Antwort...",
        submitButton: "Test einreichen & Pfad anpassen",
        generating: "Prüfer generiert Vorwissenstest...",
        evaluating: "Prüfer bewertet Vorwissen..."
    },

    // P3: Path Review
    p3: {
        title: "Lernpfad-Übersicht (P3)",
        description: "Hier ist Ihr personalisierter Lernpfad. Sie können Konzepte als 'Bekannt' markieren, um sie zu überspringen.",
        conceptStatus: {
            open: "Offen",
            active: "Aktiv",
            mastered: "Beherrscht",
            skipped: "Übersprungen",
            repeat: "Wiederholen"
        },
        bloomLevel: "Bloom-Stufe",
        markAsKnown: "Als bekannt markieren",
        startLearning: "Lernpfad starten"
    },

    // P5: Learning
    p5: {
        title: "Lernphase:",
        tutorChat: "Tutor Chat",
        chatPlaceholder: "Fragen Sie den Tutor...",
        remediationPlaceholder: "Welches Fundament fehlt Ihnen? (P5.5)",
        remediationHint: "Geben Sie das fehlende Konzept ein, um den Pfad zu korrigieren.",
        reportGap: "Fundament fehlt / Lücke melden (P5.5)",
        understood: "Konzept verstanden (P6 starten)",
        user: "Nutzer"
    },

    // P6: Test
    p6: {
        title: "Wissenstest (P6)",
        description: "Beantworten Sie die folgenden Fragen, um Ihr Verständnis zu überprüfen.",
        yourAnswer: "Ihre Antwort:",
        submitTest: "Test einreichen",
        generating: "Kurator generiert Test...",
        evaluating: "Test wird bewertet..."
    },

    // P7: Evaluation & Progression
    p7: {
        progression: {
            title: "Test bestanden! 🎉",
            description: "Glückwunsch! Sie haben das Konzept gemeistert.",
            score: "Score:",
            nextConcept: "Weiter zum nächsten Konzept"
        },
        goalComplete: {
            title: "Lernziel erreicht! 🎓",
            congratulations: "Herzlichen Glückwunsch!",
            description: "Sie haben alle Konzepte erfolgreich gemeistert.",
            lastTest: "Letzter Test:",
            newGoal: "Neues Ziel setzen",
            reviewPath: "Lernpfad überprüfen"
        },
        remediation: {
            title: "Wiederholung empfohlen",
            description: "Keine Sorge! Lernen ist ein Prozess.",
            score: "Score:",
            repeatMaterial: "Material wiederholen",
            requestHelp: "Tutor um Hilfe bitten",
            skipConcept: "Konzept überspringen (nicht empfohlen)"
        },
        detailedEvaluation: "Detaillierte Auswertung:",
        yourAnswerLabel: "Ihre Antwort:",
        correctAnswer: "Richtige Antwort:"
    },

    // Session Management
    session: {
        saveBtn: "Speichern",
        loadBtn: "Laden",
        save: "Fortschritt speichern",
        load: "Fortschritt laden",
        saved: "Fortschritt erfolgreich gespeichert! ✅",
        loaded: "Session erfolgreich geladen! 📂",
        saveFailed: "Fehler beim Speichern",
        noSession: "Keine gespeicherten Sessions gefunden",
        noGoal: "Bitte erstellen Sie zuerst ein Lernziel",
        savePrompt: "Geben Sie einen Namen für diese Session ein:",
        selectPrompt: "Wählen Sie eine Session zum Laden:\n\n",
        enterNumber: "Nummer eingeben (1-",
        invalidChoice: "Ungültige Auswahl"
    },

    // Common
    common: {
        loading: "Lädt...",
        error: "Fehler",
        cancel: "Abbrechen",
        confirm: "Bestätigen",
        back: "Zurück",
        next: "Weiter",
        close: "Schließen"
    }
};
