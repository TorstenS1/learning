import { de } from './de';
import { en } from './en';

const translations = {
    de,
    en
};

// Get browser language or default to German
export const getBrowserLanguage = () => {
    const browserLang = navigator.language.split('-')[0];
    return translations[browserLang] ? browserLang : 'de';
};

// Get stored language preference
export const getStoredLanguage = () => {
    return localStorage.getItem('alis_language') || getBrowserLanguage();
};

// Get translations for a specific language
export const getTranslations = (lang = 'de') => {
    return translations[lang] || translations.de;
};

export { de, en };
