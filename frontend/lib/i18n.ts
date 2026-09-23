'use client';
import { create } from 'zustand';

type Lang = 'en' | 'hi' | 'od';

interface I18nStore {
  lang: Lang;
  setLang: (lang: Lang) => void;
}

export const useI18nStore = create<I18nStore>((set) => ({
  lang: 'en',
  setLang: (lang) => set({ lang }),
}));

const translations = {
  en: {
    'Intake Form': 'Intake Form',
    'Patient Queue': 'Patient Queue',
    'Review Note': 'Review Note',
    'Admin Panel': 'Admin Panel',
    'Login': 'Login',
    'Consent Disclaimer': 'I consent to the use of this information for triage-support demonstration purposes. Educational prototype for triage support only. Not a medical device. Not a substitute for qualified medical advice.',
    'Proceed': 'Proceed',
    'Logout': 'Logout',
    fever: 'fever',
    cough: 'cough',
    pain: 'pain',
    breathlessness: 'breathlessness'
  },
  hi: {
    'Intake Form': 'मरीज फॉर्म',
    'Patient Queue': 'मरीज कतार',
    'Review Note': 'नोट समीक्षा',
    'Admin Panel': 'व्यवस्थापक',
    'Login': 'लॉग इन',
    'Consent Disclaimer': 'मैं इस जानकारी का उपयोग ट्राईज-सपोर्ट प्रदर्शन उद्देश्यों के लिए करने की सहमति देता/देती हूँ। केवल शैक्षिक प्रोटोटाइप। चिकित्सा उपकरण नहीं।',
    'Proceed': 'आगे बढ़ें',
    'Logout': 'लॉग आउट',
    fever: 'बुखार',
    cough: 'खांसी',
    pain: 'दर्द',
    breathlessness: 'सांस फूलना'
  },
  od: {
    'Intake Form': 'ରୋଗୀ ଫର୍ମ',
    'Patient Queue': 'ରୋଗୀ ଧାଡ଼ି',
    'Review Note': 'ନୋଟ ସମୀକ୍ଷା',
    'Admin Panel': 'ଏଡ୍ମିନ',
    'Login': 'ଲଗ ଇନ',
    'Consent Disclaimer': 'ମୁଁ ଟ୍ରାଇଜ୍-ସପୋର୍ଟ ପ୍ରଦର୍ଶନ ଉଦ୍ଦେଶ୍ୟରେ ଏହି ସୂଚନା ବ୍ୟବହାର କରିବାକୁ ସମ୍ମତି ଦେଉଛି। କେବଳ ଶିକ୍ଷଣୀୟ ପ୍ରୋଟୋଟାଇପ୍। ମେଡିକାଲ୍ ଡିଭାଇସ୍ ନୁହେଁ।',
    'Proceed': 'ଆଗକୁ ବଢନ୍ତୁ',
    'Logout': 'ଲଗ ଆଉଟ୍',
    fever: 'ଜ୍ୱର',
    cough: 'କାଶ',
    pain: 'ଯନ୍ତ୍ରଣା',
    breathlessness: 'ଶ୍ୱାସକଷ୍ଟ'
  }
};

export const useTranslation = () => {
  const { lang } = useI18nStore();
  const t = (key: keyof typeof translations['en']) => {
    return translations[lang][key] || translations['en'][key] || key;
  };
  return { t, lang };
};
