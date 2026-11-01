import { useState, type FormEvent } from "react";
import { useTranslation } from "react-i18next";
import { useAuth } from "../auth";

export default function Login() {
  const { t, i18n } = useTranslation();
  const { login, signup } = useAuth();
  const [mode, setMode] = useState<"login" | "signup">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setErr("");
    setBusy(true);
    try {
      if (mode === "login") await login(email, password);
      else await signup(email, password, name || undefined);
    } catch (x) {
      setErr((x as Error).message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="login">
      <form className="card login-card" onSubmit={submit}>
        <h1>🌿 {t("app.name")}</h1>
        <p className="muted">{t("app.tagline")}</p>
        {mode === "signup" && (
          <label>{t("auth.name")}<input value={name} onChange={(e) => setName(e.target.value)} /></label>
        )}
        <label>{t("auth.email")}
          <input type="email" required value={email} autoComplete="email" onChange={(e) => setEmail(e.target.value)} />
        </label>
        {mode === "signup" && <p className="small muted">{t("auth.emailHint")}</p>}
        <label>{t("auth.password")}
          <input type="password" required minLength={mode === "signup" ? 8 : 1} value={password}
            autoComplete={mode === "login" ? "current-password" : "new-password"}
            onChange={(e) => setPassword(e.target.value)} />
        </label>
        {err && <div className="error">{err}</div>}
        <button className="btn primary" disabled={busy}>{mode === "login" ? t("auth.login") : t("auth.signup")}</button>
        <div className="row between">
          <button type="button" className="link" onClick={() => setMode(mode === "login" ? "signup" : "login")}>
            {mode === "login" ? t("auth.toSignup") : t("auth.toLogin")}
          </button>
          <button type="button" className="link" onClick={() => i18n.changeLanguage(i18n.language === "zh" ? "en" : "zh")}>
            {i18n.language === "zh" ? "English" : "中文"}
          </button>
        </div>
      </form>
    </div>
  );
}
