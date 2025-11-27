/**
 * ALIS Backend API Service
 * Handles all HTTP communication with the Flask backend.
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';

/**
 * Generic API call wrapper with error handling
 */
async function apiCall(endpoint, payload = null, method = 'POST') {
    const url = `${API_BASE_URL}${endpoint}`;

    const options = {
        method,
        headers: {
            'Content-Type': 'application/json',
        },
    };

    if (payload && method !== 'GET') {
        options.body = JSON.stringify(payload);
    }

    try {
        const response = await fetch(url, options);

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.message || `HTTP ${response.status}: ${response.statusText}`);
        }

        return await response.json();
    } catch (error) {
        console.error(`API call failed [${endpoint}]:`, error);
        throw error;
    }
}

/**
 * ALIS API Service
 */
export const alisAPI = {
    /**
     * Health check
     */
    async healthCheck() {
        return apiCall('/health', null, 'GET');
    },

    /**
     * P1/P3: Start goal setting and path creation
     * @param {string} userId - User identifier
     * @param {string} userInput - Learning goal description
     * @param {object} userProfile - User preferences
     */
    async startGoal(userId, userInput, userProfile = {}) {
        return apiCall('/start_goal', {
            userId,
            userInput,
            userProfile: {
                stylePreference: userProfile.stylePreference || 'Analogien-basiert',
                paceWPM: userProfile.paceWPM || 180,
                ...userProfile
            }
        });
    },

    /**
     * P4: Get learning material for current concept
     * @param {string} userId - User identifier
     * @param {string} goalId - Goal identifier
     * @param {array} pathStructure - Current learning path
     * @param {object} currentConcept - Current concept being studied
     * @param {object} userProfile - User preferences
     */
    async getMaterial(userId, goalId, pathStructure, currentConcept, userProfile) {
        return apiCall('/get_material', {
            userId,
            goalId,
            pathStructure,
            currentConcept,
            userProfile
        });
    },

    /**
     * P5: Chat with tutor
     * @param {string} userId - User identifier
     * @param {string} goalId - Goal identifier
     * @param {string} userInput - Chat message
     * @param {object} currentConcept - Current concept
     */
    async chat(userId, goalId, userInput, currentConcept) {
        return apiCall('/chat', {
            userId,
            goalId,
            userInput,
            currentConcept
        });
    },

    /**
     * P5.5 Part 1: Diagnose knowledge gap
     * @param {string} userId - User identifier
     * @param {string} goalId - Goal identifier
     * @param {array} pathStructure - Current learning path
     * @param {object} currentConcept - Current concept
     */
    async diagnoseLuecke(userId, goalId, pathStructure, currentConcept) {
        return apiCall('/diagnose_luecke', {
            userId,
            goalId,
            pathStructure,
            currentConcept
        });
    },

    /**
     * P5.5 Part 2: Perform path surgery (remediation)
     * @param {string} userId - User identifier
     * @param {string} goalId - Goal identifier
     * @param {string} userInput - Missing concept name
     * @param {array} pathStructure - Current learning path
     * @param {object} currentConcept - Current concept
     */
    async performRemediation(userId, goalId, userInput, pathStructure, currentConcept) {
        return apiCall('/perform_remediation', {
            userId,
            goalId,
            userInput,
            pathStructure,
            currentConcept,
            remediationNeeded: true
        });
    },

    /**
     * P6: Generate test questions
     * @param {string} userId - User identifier
     * @param {string} goalId - Goal identifier
     * @param {object} currentConcept - Current concept
     * @param {object} userProfile - User preferences
     */
    async generateTest(userId, goalId, currentConcept, userProfile) {
        return apiCall('/generate_test', {
            userId,
            goalId,
            currentConcept,
            userProfile
        });
    }
};

export default alisAPI;
