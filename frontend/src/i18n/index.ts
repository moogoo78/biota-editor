import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import en from "./en";
import zh from "./zh";

const KEY = "biotaeditor.lang";
let lng = "zh";
try { lng = localStorage.getItem(KEY) || (navigator.language.startsWith("zh") ? "zh" : "en"); } catch { /* */ }

i18n.use(initReactI18next).init({
  resources: { en: { translation: en }, zh: { translation: zh } },
  lng,
  fallbackLng: "en",
  interpolation: { escapeValue: false },
});
i18n.on("languageChanged", (l) => { try { localStorage.setItem(KEY, l); } catch { /* */ } });

export default i18n;
