import React, { useState, useEffect } from 'react';
import { Loader2, Zap, LayoutList, BookOpen, MessageCircle, AlertTriangle, ArrowRight, CheckCircle, XCircle, ArrowLeft } from 'lucide-react';
import alisAPI from './services/alisAPI';

// ==============================================================================
// ALTERNATIVE: Browser History für Phase Navigation nutzen
// ==============================================================================

const AppWithHistory = () => {
    const [phase, setPhase] = useState('P1_GOAL_SETTING');
    const [phaseHistory, setPhaseHistory] = useState(['P1_GOAL_SETTING']);

    // Sync phase with browser history
    useEffect(() => {
        const handlePopState = (e) => {
            if (e.state && e.state.phase) {
                setPhase(e.state.phase);
            }
        };

        // Initialize history
        window.history.replaceState({ phase: 'P1_GOAL_SETTING' }, '', '');
        window.addEventListener('popstate', handlePopState);

        return () => {
            window.removeEventListener('popstate', handlePopState);
        };
    }, []);

    // Helper to navigate to new phase
    const navigateToPhase = (newPhase) => {
        setPhase(newPhase);
        setPhaseHistory([...phaseHistory, newPhase]);
        window.history.pushState({ phase: newPhase }, '', '');
    };

    // Manual back button
    const goBack = () => {
        if (phaseHistory.length > 1) {
            window.history.back();
        }
    };

    // Render back button in UI
    const renderBackButton = () => {
        if (phaseHistory.length > 1) {
            return (
                <button
                    onClick={goBack}
                    className="flex items-center px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition duration-150"
                >
                    <ArrowLeft className="w-4 h-4 mr-2" />
                    Zurück
                </button>
            );
        }
        return null;
    };

    // Beispiel: Phase-Transition mit History
    const startGoalSetting = async () => {
        // ... API call ...
        navigateToPhase('P3_PATH_REVIEW'); // Statt setPhase
    };

    return (
        <div className="min-h-screen bg-gray-100 font-sans p-4">
            {/* Back Button in Header */}
            <div className="mb-4">
                {renderBackButton()}
            </div>

            {/* Phase Rendering */}
            {phase === 'P1_GOAL_SETTING' && <div>Goal Setting UI</div>}
            {phase === 'P3_PATH_REVIEW' && <div>Path Review UI</div>}
            {/* ... weitere Phasen ... */}
        </div>
    );
};

export default AppWithHistory;
