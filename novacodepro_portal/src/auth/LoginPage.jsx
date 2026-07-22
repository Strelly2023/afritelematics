import React, { useState } from "react";

const LOGIN_ROLES = [
  "ADMIN", "DEVELOPER", "PRODUCT_MANAGER", "BUSINESS_ANALYST", "UI_UX_DESIGNER", "PROJECT_MANAGER",
  "ARCHITECT", "QA_ENGINEER", "DEVOPS_ENGINEER", "CUSTOMER_SUPPORT", "OPERATIONS_TEAM", "BRAND_TEAM",
  "COMPLIANCE_TEAM", "AUDIT_TEAM", "SECURITY_ENGINEER", "INCIDENT_RESPONSE_TEAM", "DATA_ARCHITECT",
  "DATA_ENGINEER", "DATABASE_ENGINEER", "AI_ML_ENGINEER", "DATA_SCIENTIST", "PRIVACY_COMPLIANCE",
  "RISK_MANAGEMENT", "LEGAL", "EXTERNAL_REGULATOR",
];

export function LoginPage({
  email,
  password,
  role,
  error,
  status,
  onEmailChange,
  onPasswordChange,
  onRoleChange,
  onSubmit,
  onHome,
  onUnavailable,
}) {
  const [showPassword, setShowPassword] = useState(false);
  const [rememberDevice, setRememberDevice] = useState(false);
  const [theme, setTheme] = useState("system");
  const [language, setLanguage] = useState("en-AU");
  const busy = status === "submitting";

  return (
    <div className="next-auth-shell" data-theme={theme} data-testid="novacodepro-login-page">
      <a className="skip-link" href="#login-form">Skip to sign in</a>
      <header className="next-auth-header">
        <button className="public-brand" type="button" onClick={onHome} aria-label="NovaCodePro home">
          <img src="/novacodepro/brand/NOVACODEPRO.webp" alt="" /><span>NovaCodePro</span>
        </button>
        <div>
          <label className="public-select"><span className="sr-only">Theme</span><select value={theme} onChange={(event) => setTheme(event.target.value)} aria-label="Theme"><option value="system">System theme</option><option value="light">Light</option><option value="dark">Dark</option><option value="contrast">High contrast</option></select></label>
          <label className="public-select"><span className="sr-only">Language</span><select value={language} onChange={(event) => setLanguage(event.target.value)} aria-label="Language"><option value="en-AU">English</option><option value="fr">Français</option><option value="sw">Kiswahili</option></select></label>
        </div>
      </header>

      <main className="next-auth-main">
        <section className="next-auth-story" aria-labelledby="login-story-title">
          <div className="public-kicker"><span /> Secure enterprise design</div>
          <h1 id="login-story-title">Design with clarity.<br /><em>Deliver with confidence.</em></h1>
          <p>Continue designing, governing, and delivering digital products from one trusted NovaCodePro workspace.</p>
          <div className="auth-visual" aria-label="NovaCodePro governed design workflow preview">
            <div className="auth-visual-canvas"><span className="auth-node first">Requirements<small>24 linked</small></span><i /><span className="auth-node second">Wireframes<small>12 screens</small></span><i /><span className="auth-node third">Approval<small>Review ready</small></span></div>
            <div className="auth-visual-score"><span>Accessibility review</span><strong>98</strong><small>Evidence attached</small></div>
          </div>
          <ul className="auth-trust-list"><li>NovaID protected</li><li>Tenant isolated</li><li>Audit recorded</li></ul>
        </section>

        <section className="next-auth-card" aria-labelledby="login-title">
          <div className="auth-card-heading"><p>WELCOME TO NOVACODEPRO</p><h2 id="login-title">Sign in to continue</h2><span>Access your permitted projects, design systems, reviews, and handoff workspace.</span></div>
          <form id="login-form" onSubmit={(event) => onSubmit(event, rememberDevice)} noValidate>
            <label className="next-auth-field"><span>Email or username</span><input type="text" value={email} onChange={(event) => onEmailChange(event.target.value)} autoComplete="username" required aria-invalid={Boolean(error)} /></label>
            <label className="next-auth-field"><span>Password</span><div className="password-control"><input type={showPassword ? "text" : "password"} value={password} onChange={(event) => onPasswordChange(event.target.value)} autoComplete="current-password" required aria-invalid={Boolean(error)} /><button type="button" onClick={() => setShowPassword((value) => !value)} aria-label={showPassword ? "Hide password" : "Show password"}>{showPassword ? "Hide" : "Show"}</button></div></label>
            <label className="next-auth-field"><span>Workspace role</span><select value={role} onChange={(event) => onRoleChange(event.target.value)}>{LOGIN_ROLES.map((item) => <option key={item} value={item}>{item.replaceAll("_", " ")}</option>)}</select></label>
            <div className="auth-form-options"><label><input type="checkbox" checked={rememberDevice} onChange={(event) => setRememberDevice(event.target.checked)} /> Remember this device</label><button type="button" onClick={() => onUnavailable("Password recovery is managed by your NovaID administrator.")}>Forgot password?</button></div>
            {error ? <div className="next-auth-error" role="alert"><strong>We couldn’t sign you in.</strong><span>{error}</span></div> : null}
            <button type="submit" className="next-auth-submit" disabled={busy}>{busy ? <><i className="auth-spinner" /> Verifying identity…</> : "Sign in securely"}</button>
            <div className="auth-divider"><span>or continue with</span></div>
            <div className="auth-provider-grid"><button type="button" onClick={() => onUnavailable("Passkey sign-in is not enabled for this NovaCodePro workspace.")}><span aria-hidden="true">◇</span> Passkey</button><button type="button" onClick={() => onUnavailable("Single sign-on is not enabled for this NovaCodePro workspace.")}><span aria-hidden="true">◫</span> Enterprise SSO</button></div>
            <p className="auth-policy-note">MFA and adaptive verification continue automatically when required by your NovaID tenant policy.</p>
          </form>
          <footer className="auth-card-footer"><button type="button" onClick={() => onUnavailable("Account provisioning is managed by your organisation.")}>Request access</button><span>·</span><a href="#privacy">Privacy</a><span>·</span><a href="#terms">Terms</a><span>·</span><button type="button" onClick={() => onUnavailable("Contact your NovaCodePro workspace administrator for support.")}>Help</button></footer>
        </section>
      </main>
    </div>
  );
}
