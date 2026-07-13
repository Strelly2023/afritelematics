import React from "react";

function normalizePairs(value) {
  if (Array.isArray(value)) {
    return value
      .map((item) => {
        if (Array.isArray(item) && item.length >= 2) {
          return [String(item[0]), String(item[1])];
        }
        if (item && typeof item === "object") {
          const label = item.label ?? item.name ?? item.title ?? item.id ?? "";
          const metricValue = item.value ?? item.detail ?? item.status ?? item.count ?? "";
          if (label || metricValue) {
            return [String(label), String(metricValue)];
          }
        }
        return null;
      })
      .filter(Boolean);
  }
  if (value && typeof value === "object") {
    return Object.entries(value).map(([label, metricValue]) => [String(label), String(metricValue)]);
  }
  return [];
}

function SurfaceMetricGrid({ metrics }) {
  const pairs = normalizePairs(metrics);
  return (
    <div className="role-surface-metric-grid">
      {pairs.map(([label, value]) => (
        <div className="role-surface-metric" key={label}>
          <span>{label}</span>
          <strong>{value}</strong>
        </div>
      ))}
    </div>
  );
}

function SurfaceList({ section }) {
  return (
    <div className="role-surface-list-block">
      <p className="section-label">{section.label}</p>
      <div className="role-surface-list">
        {section.rows.length ? (
          section.rows.map((item) => (
            <div className="role-surface-list-item" key={`${section.label}-${item.title}`}>
              <strong>{item.title}</strong>
              <span>{item.detail}</span>
            </div>
          ))
        ) : (
          <div className="role-surface-empty">No items available.</div>
        )}
      </div>
    </div>
  );
}

export function RoleWorkspaceWindows({ model, activeSurfaceId, onFocusSurface, onRunCommand }) {
  const activeSurface = model.windows.find((surface) => surface.id === activeSurfaceId) ?? model.windows[0];

  return (
    <section className="role-workspace-band">
      <div className="band-header">
        <div>
          <p className="section-label">Role operating environment</p>
          <h2>{model.headerTitle}</h2>
          <p className="window-summary">{model.headerSummary}</p>
        </div>
        <div className="workspace-tabs role-workspace-tabs" aria-label="Role workspace windows">
          {model.windows.map((surface) => (
            <button
              key={surface.id}
              type="button"
              className={surface.id === activeSurfaceId ? "workspace-tab active" : "workspace-tab"}
              onClick={() => onFocusSurface(surface)}
            >
              {surface.label}
            </button>
          ))}
        </div>
      </div>

      <div className="role-window-grid">
        {model.windows.map((surface) => (
          <article
            className={surface.id === activeSurfaceId ? "role-window-card active" : "role-window-card"}
            id={surface.anchorId}
            key={surface.id}
          >
            <div className="window-head">
              <div>
                <p className="section-label">{surface.label}</p>
                <h3>{surface.title}</h3>
              </div>
              <span className="status-pill">{surface.status}</span>
            </div>
            <p className="window-summary">{surface.summary}</p>
            <SurfaceMetricGrid metrics={surface.metrics} />
            <div className="role-surface-highlights">
              {surface.highlights.map((item) => (
                <div className="role-surface-highlight" key={`${surface.id}-${item}`}>
                  {item}
                </div>
              ))}
            </div>
            {surface.lists.map((section) => (
              <SurfaceList key={`${surface.id}-${section.label}`} section={section} />
            ))}
            <div className="role-surface-actions">
              {surface.actions.map((action) => (
                <button
                  key={action.label}
                  type="button"
                  className="toolbar-chip"
                  onClick={() => onRunCommand(action.command)}
                >
                  {action.label}
                </button>
              ))}
            </div>
          </article>
        ))}
      </div>

      <div className="role-window-detail">
        <div className="window-head compact">
          <div>
            <p className="section-label">Focused window</p>
            <h3>{activeSurface.title}</h3>
          </div>
          <span className="status-pill">{activeSurface.status}</span>
        </div>
        <div className="role-window-detail-grid">
          <div className="role-window-detail-copy">
            <p className="studio-note">{activeSurface.summary}</p>
            <div className="role-surface-highlights compact">
              {activeSurface.highlights.slice(0, 2).map((item) => (
                <div className="role-surface-highlight" key={`detail-${item}`}>
                  {item}
                </div>
              ))}
            </div>
          </div>
          <div className="role-window-detail-actions">
            <p className="section-label">Connected actions</p>
            <div className="role-surface-actions compact">
              {activeSurface.actions.map((action) => (
                <button
                  key={`detail-${action.label}`}
                  type="button"
                  className="toolbar-chip"
                  onClick={() => onRunCommand(action.command)}
                >
                  {action.label}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
