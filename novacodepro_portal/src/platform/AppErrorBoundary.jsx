import React from "react";

import { ROUTES } from "./routes.js";
import { clearNovaCodeProSessionState } from "./sessionState.js";
import { NOVACODEPRO_BUILD_INFO } from "./version.js";

function createReferenceId() {
  return `NCP-UI-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8).toUpperCase()}`;
}

function safeMessage(error) {
  if (!error) {
    return "NovaCodePro could not load this workspace.";
  }
  const message = error instanceof Error ? error.message : String(error);
  if (/chunkloaderror|loading css chunk failed|failed to fetch dynamically imported module/i.test(message)) {
    return "A portal update could not load. Reload the application to try again.";
  }
  return "NovaCodePro could not load this workspace.";
}

export class AppErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      error: null,
      errorId: null,
      resetCount: 0,
    };
  }

  componentDidMount() {
    this._handleError = (event) => {
      const error = event.error || new Error(event.message || "Uncaught application error");
      this.setState({ error, errorId: createReferenceId() });
    };
    this._handleRejection = (event) => {
      const reason = event.reason instanceof Error ? event.reason : new Error(String(event.reason || "Unhandled promise rejection"));
      this.setState({ error: reason, errorId: createReferenceId() });
    };
    window.addEventListener("error", this._handleError);
    window.addEventListener("unhandledrejection", this._handleRejection);
  }

  componentWillUnmount() {
    window.removeEventListener("error", this._handleError);
    window.removeEventListener("unhandledrejection", this._handleRejection);
  }

  static getDerivedStateFromError(error) {
    return { error, errorId: createReferenceId() };
  }

  componentDidCatch(error, info) {
    this._reportError(error, info?.componentStack || "");
  }

  _reportError(error, componentStack) {
    try {
      window.console.error("NovaCodePro application error", {
        error,
        componentStack,
        build: NOVACODEPRO_BUILD_INFO,
      });
    } catch {
      // Ignore logging failures. The recovery screen must still render.
    }
  }

  handleRetry = () => {
    this.setState((state) => ({ error: null, errorId: null, resetCount: state.resetCount + 1 }));
  };

  handleReload = () => {
    window.location.replace(ROUTES.dashboard);
  };

  handleSignIn = async () => {
    try {
      await fetch("/v1/novacodepro/session/logout", { method: "POST", credentials: "include" });
    } catch {
      // Ignore sign-out failures.
    }
    clearNovaCodeProSessionState();
    window.location.assign(ROUTES.loginWithReason("session_expired"));
  };

  handleClearSession = async () => {
    try {
      await fetch("/v1/novacodepro/session/logout", { method: "POST", credentials: "include" });
    } catch {
      // Ignore sign-out failures.
    }
    clearNovaCodeProSessionState();
    window.location.assign(ROUTES.loginWithReason("session_expired"));
  };

  render() {
    const { error, errorId, resetCount } = this.state;
    if (error) {
      return (
        <div className="auth-shell">
          <header className="auth-topbar">
            <div className="brand-block">
              <div className="brand-mark">N</div>
              <div>
                <p className="eyebrow">NovaCodePro recovery screen</p>
                <strong>NovaCodePro</strong>
              </div>
            </div>
          </header>
          <main className="auth-panel">
            <section className="auth-copy">
              <p className="section-label">Application recovery</p>
              <h1>NovaCodePro could not load this workspace.</h1>
              <p className="hero-summary">{safeMessage(error)}</p>
              <p className="auth-error">Reference: {errorId}</p>
              <p className="hero-summary">
                Version {NOVACODEPRO_BUILD_INFO.version} · Build {NOVACODEPRO_BUILD_INFO.build_id} · Commit{" "}
                {NOVACODEPRO_BUILD_INFO.commit}
              </p>
            </section>
            <div className="auth-form">
              <button type="button" className="novaid-button" onClick={this.handleRetry}>
                Retry
              </button>
              <button type="button" className="secondary-action" onClick={this.handleReload}>
                Reload application
              </button>
              <button type="button" className="secondary-action" onClick={this.handleSignIn}>
                Sign in again
              </button>
              <button type="button" className="secondary-action" onClick={this.handleClearSession}>
                Clear local session
              </button>
            </div>
          </main>
        </div>
      );
    }
    const child = React.Children.only(this.props.children);
    return React.cloneElement(child, { key: resetCount });
  }
}
