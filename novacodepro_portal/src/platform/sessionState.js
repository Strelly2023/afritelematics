const NOVACODEPRO_SESSION_KEYS = [
  "novacodepro.session.summary",
  "novacodepro.activeRole",
  "novacodepro.workspace",
  "novacodepro.workspace.cache",
];

export function clearNovaCodeProSessionState() {
  try {
    for (const key of NOVACODEPRO_SESSION_KEYS) {
      window.sessionStorage?.removeItem(key);
      window.localStorage?.removeItem(key);
    }
  } catch {
    // Ignore storage cleanup failures.
  }
}
