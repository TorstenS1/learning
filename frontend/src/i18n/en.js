export const en = {
    // P1: Goal Setting
    p1: {
        title: "ALIS: Goal Contract (P1)",
        description: "Define your learning goal. The **Architect** will standardize it into a measurable **SMART contract**.",
        placeholder: "Example: I want to implement multi-agent systems in logistics.",
        buttonSubmit: "Create SMART Contract",
        buttonSubmitting: "Negotiating goal...",
        currentMessage: "Current LLM Message:"
    },

    // P2: Prior Knowledge
    p2: {
        choiceTitle: "Test Prior Knowledge? (P2)",
        choiceDescription: "Would you like to take a short test to automatically skip concepts you already know?",
        choiceYes: "Yes, test prior knowledge",
        choiceNo: "No, go directly to path",
        testTitle: "Prior Knowledge Test (P2)",
        testDescription: "Please answer the following questions so we can adapt your learning path.",
        yourAnswer: "Your answer...",
        submitButton: "Submit test & adapt path",
        generating: "Examiner generating prior knowledge test...",
        evaluating: "Examiner evaluating prior knowledge..."
    },

    // P3: Path Review
    p3: {
        title: "Learning Path Overview (P3)",
        description: "Here is your personalized learning path. You can mark concepts as 'Known' to skip them.",
        conceptStatus: {
            open: "Open",
            active: "Active",
            mastered: "Mastered",
            skipped: "Skipped",
            repeat: "Repeat"
        },
        bloomLevel: "Bloom Level",
        markAsKnown: "Mark as known",
        startLearning: "Start learning path"
    },

    // P5: Learning
    p5: {
        title: "Learning Phase:",
        tutorChat: "Tutor Chat",
        chatPlaceholder: "Ask the tutor...",
        remediationPlaceholder: "What foundation is missing? (P5.5)",
        remediationHint: "Enter the missing concept to correct the path.",
        reportGap: "Report missing foundation / gap (P5.5)",
        understood: "Concept understood (start P6)",
        user: "User"
    },

    // P6: Test
    p6: {
        title: "Knowledge Test (P6)",
        description: "Answer the following questions to verify your understanding.",
        yourAnswer: "Your answer:",
        submitTest: "Submit test",
        generating: "Curator generating test...",
        evaluating: "Evaluating test..."
    },

    // P7: Evaluation & Progression
    p7: {
        progression: {
            title: "Test Passed! 🎉",
            description: "Congratulations! You have mastered the concept.",
            score: "Score:",
            nextConcept: "Continue to next concept"
        },
        goalComplete: {
            title: "Learning Goal Achieved! 🎓",
            congratulations: "Congratulations!",
            description: "You have successfully mastered all concepts.",
            lastTest: "Last Test:",
            newGoal: "Set new goal",
            reviewPath: "Review learning path"
        },
        remediation: {
            title: "Review Recommended",
            description: "Don't worry! Learning is a process.",
            score: "Score:",
            repeatMaterial: "Review material",
            requestHelp: "Ask tutor for help",
            skipConcept: "Skip concept (not recommended)"
        },
        detailedEvaluation: "Detailed Evaluation:",
        yourAnswerLabel: "Your answer:",
        correctAnswer: "Correct answer:"
    },

    // Common
    common: {
        loading: "Loading...",
        error: "Error",
        cancel: "Cancel",
        confirm: "Confirm",
        back: "Back",
        next: "Next",
        close: "Close"
    }
};
