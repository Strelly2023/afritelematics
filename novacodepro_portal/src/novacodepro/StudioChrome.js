import React, { useMemo, useState } from "react";

const h = React.createElement;

function normalizeItems(items) {
  return Array.isArray(items) ? items.filter(Boolean) : [];
}

function MenuGroup({ menu, isOpen, onToggle, onClose }) {
  const entries = normalizeItems(menu?.items);
  return h(
    "details",
    {
      className: "studio-menu",
      open: isOpen,
      onToggle: (event) => onToggle(menu?.id, event.currentTarget.open),
    },
    h(
      "summary",
      { className: "studio-menu-trigger" },
      h("span", null, menu?.label),
      menu?.shortcut ? h("small", null, menu.shortcut) : null,
    ),
    h(
      "div",
      { className: "studio-menu-popover", role: "menu", "aria-label": `${menu?.label || "Menu"} commands` },
      entries.length
        ? entries.map((item) =>
            h(
              "button",
              {
                key: item.id || item.label,
                type: "button",
                className: "studio-menu-item",
                role: "menuitem",
                disabled: item.disabled,
                onClick: () => {
                  item.action?.();
                  onClose();
                },
              },
              h("strong", null, item.label),
              h("span", null, item.description || item.shortcut || "Command"),
            ),
          )
        : h(
            "div",
            { className: "studio-menu-empty" },
            h("strong", null, "No commands"),
            h("span", null, "Nothing is exposed for this menu yet."),
          ),
    ),
  );
}

function ActivityButton({ item, active, onClick }) {
  return h(
    "button",
    {
      type: "button",
      className: active ? "studio-activity-item active" : "studio-activity-item",
      onClick,
      "aria-pressed": active,
      title: item.description,
    },
    h("span", { className: "studio-activity-icon", "aria-hidden": "true" }, item.icon),
    h(
      "span",
      { className: "studio-activity-label" },
      item.label,
      typeof item.count === "number" ? h("small", null, item.count) : null,
    ),
  );
}

export function StudioChrome({
  title,
  subtitle,
  menus = [],
  activityItems = [],
  contextItems = [],
  statusItems = [],
  primaryAction,
  primaryActionLabel = "Command palette",
  onOpenPalette,
  onActivityChange,
  activeActivityId,
  children,
}) {
  const [openMenuId, setOpenMenuId] = useState("");
  const activeMenu = useMemo(() => normalizeItems(menus).find((menu) => menu.id === openMenuId) || null, [menus, openMenuId]);

  return h(
    "section",
    { className: "studio-chrome", "aria-label": title || "NovaCodePro Studio workspace" },
    h(
      "div",
      { className: "studio-menu-bar" },
      h(
        "div",
        { className: "studio-menu-bar-core", role: "menubar", "aria-label": "NovaCodePro Studio menus" },
        ...normalizeItems(menus).map((menu) =>
          h(MenuGroup, {
            key: menu.id,
            menu,
            isOpen: activeMenu?.id === menu.id,
            onToggle: (menuId, open) => setOpenMenuId(open ? menuId : ""),
            onClose: () => setOpenMenuId(""),
          }),
        ),
      ),
      h(
        "div",
        { className: "studio-menu-bar-actions" },
        primaryAction ? h("button", { type: "button", className: "toolbar-chip", onClick: primaryAction }, primaryActionLabel) : null,
        onOpenPalette ? h("button", { type: "button", className: "toolbar-chip", onClick: onOpenPalette }, "Command palette") : null,
        title ? h("span", { className: "studio-menu-bar-title" }, title) : null,
      ),
    ),
    h(
      "div",
      { className: "studio-context-strip", "aria-label": "Studio context" },
      title
        ? h(
            "div",
            { className: "studio-context-chip" },
            h("span", null, "Workspace"),
            h("strong", null, title),
          )
        : null,
      subtitle
        ? h(
            "div",
            { className: "studio-context-chip" },
            h("span", null, "Context"),
            h("strong", null, subtitle),
          )
        : null,
      ...normalizeItems(contextItems).map((item) =>
        h(
          "div",
          { className: "studio-context-chip", key: item.label },
          h("span", null, item.label),
          h("strong", null, item.value),
        ),
      ),
    ),
    h(
      "div",
      { className: "studio-workbench" },
      h(
        "nav",
        { className: "studio-activity-bar", "aria-label": "Studio navigation" },
        ...normalizeItems(activityItems).map((item) =>
          h(ActivityButton, {
            key: item.id || item.label,
            item,
            active: item.id === activeActivityId,
            onClick: () => onActivityChange?.(item),
          }),
        ),
      ),
      h("div", { className: "studio-workbench-main" }, children),
    ),
    normalizeItems(statusItems).length
      ? h(
          "footer",
          { className: "studio-status-bar", "aria-label": "Studio status" },
          ...statusItems.map((item) =>
            h(
              "span",
              { className: item.tone ? `studio-status-item tone-${item.tone}` : "studio-status-item", key: item.label },
              h("strong", null, item.label),
              h("span", null, item.value),
            ),
          ),
        )
      : null,
  );
}

export default StudioChrome;
