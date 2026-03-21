import React, { createContext, useContext, useState } from 'react';
import type { ReactNode } from 'react';

type Language = 'en' | 'hi' | 'ta';

export const translations = {
  en: {
    dashboard: "Intelligence Home",
    ontology: "Ontology Graph",
    map: "Global Map",
    infrastructure: "Infrastructure",
    lens: "Constituency Lens",
    schemes: "Scheme Linkage",
    workers: "Worker Ops",
    comms: "Communications",
    alerts: "Risk Alerts",
    strategic_brain: "Strategic Brain",
    active_node: "ACTIVE NODE",
    auth_level: "Auth Level: ALPHA-SEC",
    op_strategist: "Operational Strategist"
  },
  hi: {
    dashboard: "इंटेलिजेंस होम",
    ontology: "ऑन्टोलॉजी ग्राफ",
    map: "वैश्विक मानचित्र",
    infrastructure: "बुनियादी ढांचा (Infrastructure)",
    lens: "निर्वाचन क्षेत्र लेंस",
    schemes: "योजना लिंकेज (Schemes)",
    workers: "कार्यकर्ता संचालन",
    comms: "संचार (Comms)",
    alerts: "जोखिम अलर्ट",
    strategic_brain: "रणनीतिक मस्तिष्क",
    active_node: "सक्रिय नोड",
    auth_level: "अधिकार स्तर (Auth): अल्फा",
    op_strategist: "परिचालन रणनीतिकार"
  },
  ta: {
    dashboard: "நுண்ணறிவு முகப்பு",
    ontology: "பொருண்மையியல் வரைபடம்",
    map: "உலகளாவிய வரைபடம்",
    infrastructure: "உள்கட்டமைப்பு",
    lens: "தொகுதி லென்ஸ்",
    schemes: "திட்ட இணைப்பு",
    workers: "பணியாளர் செயல்பாடுகள்",
    comms: "தொடர்புகள்",
    alerts: "ஆபத்து எச்சரிக்கைகள்",
    strategic_brain: "மூலோபாய மூளை",
    active_node: "செயலில் உள்ள முனை",
    auth_level: "அங்கீகார நிலை: ஆல்பா",
    op_strategist: "செயல்பாட்டு வியூகவாதி"
  }
};

interface LanguageContextType {
  lang: Language;
  setLang: (lang: Language) => void;
  t: (key: keyof typeof translations.en) => string;
}

const LanguageContext = createContext<LanguageContextType | undefined>(undefined);

export const LanguageProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [lang, setLang] = useState<Language>('en');

  const t = (key: keyof typeof translations.en) => {
    return translations[lang][key] || translations.en[key];
  };

  return (
    <LanguageContext.Provider value={{ lang, setLang, t }}>
      {children}
    </LanguageContext.Provider>
  );
};

export const useLanguage = () => {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error('useLanguage must be used within a LanguageProvider');
  }
  return context;
};
