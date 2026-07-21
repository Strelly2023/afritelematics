import React, { useEffect, useMemo, useRef, useState } from "react";

import { createNovaCodeProNcp003Api } from "../api/novacodeproNcp003Api.js";
import { createNovaCodeProNcp007Api } from "../api/novacodeproNcp007Api.js";

const h = React.createElement;

const SUPPORTED_TEXT_EXTENSIONS = new Set([
  ".js",
  ".mjs",
  ".cjs",
  ".jsx",
  ".ts",
  ".tsx",
  ".py",
  ".java",
  ".cs",
  ".go",
  ".rs",
  ".kt",
  ".kts",
  ".dart",
  ".html",
  ".htm",
  ".css",
  ".json",
  ".yml",
  ".yaml",
  ".xml",
  ".md",
  ".markdown",
  ".sql",
  ".sh",
  ".bash",
  ".ps1",
  ".dockerfile",
  ".tf",
  ".tfvars",
  ".graphql",
  ".gql",
  ".proto",
  ".txt",
]);

const SPECIAL_TEXT_FILENAMES = new Set([
  "Dockerfile",
  "Makefile",
  "README",
  "README.md",
  "LICENSE",
  "package.json",
  "pnpm-workspace.yaml",
  "pnpm-lock.yaml",
  "yarn.lock",
  "package-lock.json",
  "pyproject.toml",
  "requirements.txt",
  "Pipfile",
  "Pipfile.lock",
  "go.mod",
  "go.sum",
  "Cargo.toml",
  "Cargo.lock",
  "pom.xml",
  "build.gradle",
  "build.gradle.kts",
  "settings.gradle",
  "settings.gradle.kts",
  "composer.json",
  "terraform.tfvars",
]);

const FOLDER_SUMMARY_TYPES = [
  { type: "application", label: "Applications", matcher: (path) => /^apps?\//i.test(path) || /\/app(s)?\//i.test(path) },
  { type: "service", label: "Services", matcher: (path) => /^services?\//i.test(path) || /\/service(s)?\//i.test(path) || /\/api\//i.test(path) },
  { type: "library", label: "Libraries", matcher: (path) => /^libs?\//i.test(path) || /^packages?\//i.test(path) || /\/shared\//i.test(path) },
  { type: "package", label: "Packages", matcher: (path, name) => /package\.json$|pnpm-workspace\.yaml$|pnpm-lock\.yaml$|yarn\.lock$|package-lock\.json$|pyproject\.toml$|pom\.xml$|go\.mod$|Cargo\.toml$/i.test(path) || /^(package|library)$/i.test(name) },
  { type: "test", label: "Tests", matcher: (path) => /(^|\/)tests?\//i.test(path) || /\.(test|spec)\.[^.]+$/i.test(path) },
  { type: "documentation", label: "Documentation", matcher: (path) => /(^|\/)docs?\//i.test(path) || /\.mdx?$/i.test(path) || /\.rst$/i.test(path) },
  { type: "infrastructure", label: "Infrastructure", matcher: (path) => /(^|\/)(infra|infrastructure|deploy|deployment|k8s|kubernetes|terraform|iac)\//i.test(path) || /(^|\/)(dockerfile|compose\.(ya?ml)|.*\.tf|.*\.tfvars)$/i.test(path) },
  { type: "evidence", label: "Evidence", matcher: (path) => /(^|\/)(evidence|artifacts?|reports?)\//i.test(path) },
];

function safeJsonParse(value, fallback) {
  try {
    return JSON.parse(value);
  } catch {
    return fallback;
  }
}

function storageKey(session, workspaceId, suffix) {
  const userId = session?.user?.id || session?.user_id || "anonymous";
  const tenantId = session?.tenant?.id || session?.tenant_id || session?.organization?.id || "tenant";
  const scope = workspaceId || session?.workspace?.id || session?.workspace_id || "workspace";
  return `novacodepro.explorer.${tenantId}.${userId}.${scope}.${suffix}`;
}

function loadStoredValue(session, workspaceId, suffix, fallback) {
  if (typeof window === "undefined") return fallback;
  try {
    const raw = window.localStorage?.getItem(storageKey(session, workspaceId, suffix));
    if (!raw) return fallback;
    return safeJsonParse(raw, fallback);
  } catch {
    return fallback;
  }
}

function storeValue(session, workspaceId, suffix, value) {
  if (typeof window === "undefined") return;
  try {
    window.localStorage?.setItem(storageKey(session, workspaceId, suffix), JSON.stringify(value));
  } catch {
    // ignore persistence failures in constrained environments
  }
}

function useDebouncedValue(value, delayMs = 250) {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    if (typeof window === "undefined") {
      setDebounced(value);
      return undefined;
    }
    const handle = window.setTimeout(() => setDebounced(value), delayMs);
    return () => window.clearTimeout(handle);
  }, [delayMs, value]);
  return debounced;
}

function normalizePath(path) {
  return String(path || "")
    .replace(/\\/g, "/")
    .replace(/\/+/g, "/")
    .replace(/^\/+/, "")
    .replace(/\/+$/, "");
}

function fileExtension(path) {
  const cleaned = normalizePath(path);
  const last = cleaned.split("/").pop() || "";
  if (SPECIAL_TEXT_FILENAMES.has(last)) return last.toLowerCase();
  const dot = last.lastIndexOf(".");
  return dot >= 0 ? last.slice(dot).toLowerCase() : "";
}

function languageFromPath(path) {
  const ext = fileExtension(path);
  const mapping = {
    ".js": "JavaScript",
    ".mjs": "JavaScript",
    ".cjs": "JavaScript",
    ".jsx": "JavaScript React",
    ".ts": "TypeScript",
    ".tsx": "TypeScript React",
    ".py": "Python",
    ".java": "Java",
    ".cs": "C#",
    ".go": "Go",
    ".rs": "Rust",
    ".kt": "Kotlin",
    ".kts": "Kotlin",
    ".dart": "Dart",
    ".html": "HTML",
    ".htm": "HTML",
    ".css": "CSS",
    ".json": "JSON",
    ".yml": "YAML",
    ".yaml": "YAML",
    ".xml": "XML",
    ".md": "Markdown",
    ".markdown": "Markdown",
    ".sql": "SQL",
    ".sh": "Shell",
    ".bash": "Shell",
    ".ps1": "PowerShell",
    ".dockerfile": "Dockerfile",
    ".tf": "Terraform",
    ".tfvars": "Terraform",
    ".graphql": "GraphQL",
    ".gql": "GraphQL",
    ".proto": "Protocol Buffers",
    ".txt": "Plain text",
  };
  const basename = normalizePath(path).split("/").pop() || "";
  if (basename === "Dockerfile") return "Dockerfile";
  return mapping[ext] || "Plain text";
}

function resourceTypeForPath(path, kind = "file") {
  const normalized = normalizePath(path);
  const basename = normalized.split("/").pop() || normalized;
  if (kind === "folder") return "folder";
  if (kind === "repository") return "repository";
  if (kind === "branch") return "branch";
  if (kind === "worktree") return "worktree";
  if (kind === "organisation") return "organisation";
  if (kind === "workspace") return "workspace";
  if (kind === "product") return "product";
  if (kind === "solution") return "solution";
  if (kind === "project") return "project";
  if (kind === "application") return "application";
  if (kind === "service") return "service";
  if (kind === "library") return "library";
  if (kind === "package") return "package";
  if (kind === "dependency") return "dependency";
  if (kind === "test") return "test";
  if (kind === "infrastructure") return "infrastructure";
  if (kind === "documentation") return "documentation";
  if (kind === "evidence") return "evidence";
  if (kind === "file") {
    if (/(^|\/)tests?\//i.test(normalized) || /\.(test|spec)\.[^.]+$/i.test(normalized)) return "test";
    if (/(^|\/)docs?\//i.test(normalized) || /\.mdx?$/i.test(normalized) || /\.rst$/i.test(normalized)) return "documentation";
    if (/(^|\/)(infra|infrastructure|deploy|deployment|k8s|kubernetes|terraform|iac)\//i.test(normalized) || /(^|\/)(dockerfile|compose\.(ya?ml)|.*\.tf|.*\.tfvars)$/i.test(normalized)) return "infrastructure";
    if (/(^|\/)(evidence|artifacts?|reports?)\//i.test(normalized)) return "evidence";
    if (/package\.json$|pnpm-workspace\.yaml$|pnpm-lock\.yaml$|yarn\.lock$|package-lock\.json$|pyproject\.toml$|pom\.xml$|go\.mod$|Cargo\.toml$/i.test(normalized)) return "package";
    if (/^dependency:/i.test(basename)) return "dependency";
  }
  return kind;
}

function createExplorerResource({
  type,
  name,
  path = "",
  workspaceId,
  organizationId,
  repositoryId = "",
  projectId = "",
  parentId = "",
  hasChildren = false,
  childCount = 0,
  gitStatus = "Unavailable",
  language = "",
  sizeBytes = undefined,
  modifiedAt = "",
  isReadOnly = false,
  permissions = [],
  metadata = {},
}) {
  const id = `${type}:${workspaceId}:${path || name}`;
  return {
    id,
    type,
    name,
    path,
    parentId,
    repositoryId,
    projectId,
    workspaceId,
    organizationId,
    hasChildren,
    childCount,
    gitStatus,
    language,
    sizeBytes,
    modifiedAt,
    isReadOnly,
    permissions,
    metadata,
  };
}

function buildNestedRepositoryTree(entries, { workspaceId, organizationId, repositoryId, rootPath = "." }) {
  const rootLabel = rootPath === "." ? "Repository root" : rootPath;
  const root = createExplorerResource({
    type: "repository",
    name: rootLabel,
    path: normalizePath(rootPath),
    workspaceId,
    organizationId,
    repositoryId,
    hasChildren: true,
    childCount: entries.length,
    metadata: { scope: "repository-root", entryCount: entries.length },
  });
  const nodesByPath = new Map([[root.path || ".", { ...root, children: [] }]]);
  const sortedEntries = [...entries].sort((a, b) => String(a.path).localeCompare(String(b.path)));

  for (const entry of sortedEntries) {
    const normalized = normalizePath(entry.path);
    if (!normalized) continue;
    const parts = normalized.split("/");
    let parentPath = root.path || ".";
    let currentPath = "";
    for (let index = 0; index < parts.length; index += 1) {
      const segment = parts[index];
      currentPath = currentPath ? `${currentPath}/${segment}` : segment;
      const isLeaf = index === parts.length - 1;
      const currentNodeType = isLeaf ? "file" : "folder";
      const currentNodeId = `${currentNodeType}:${workspaceId}:${currentPath}`;
      if (!nodesByPath.has(currentPath)) {
        const node = createExplorerResource({
          type: resourceTypeForPath(currentPath, isLeaf ? "file" : "folder"),
          name: segment,
          path: currentPath,
          parentId: parentPath === "." ? root.id : `${nodesByPath.get(parentPath)?.type || "folder"}:${workspaceId}:${parentPath}`,
          workspaceId,
          organizationId,
          repositoryId,
          hasChildren: !isLeaf,
          childCount: 0,
          gitStatus: entry.git_status || entry.status || "Unavailable",
          language: isLeaf ? languageFromPath(currentPath) : "",
          sizeBytes: isLeaf ? entry.size_bytes ?? entry.sizeBytes ?? undefined : undefined,
          modifiedAt: entry.modified_at || entry.updated_at || "",
          isReadOnly: true,
          metadata: {
            extension: entry.extension || fileExtension(currentPath),
            source: "repository-tree",
          },
        });
        nodesByPath.set(currentPath, { ...node, children: [] });
      }
      const parentNode = nodesByPath.get(parentPath);
      const currentNode = nodesByPath.get(currentPath);
      if (parentNode && currentNode && !parentNode.children?.some((child) => child.id === currentNodeId)) {
        parentNode.children = parentNode.children || [];
        parentNode.children.push(currentNode);
        parentNode.hasChildren = true;
        parentNode.childCount = parentNode.children.length;
      }
      parentPath = currentPath;
    }
  }

  return nodesByPath.get(root.path || ".") || root;
}

function countByCategory(entries) {
  const counts = Object.fromEntries(FOLDER_SUMMARY_TYPES.map((item) => [item.type, 0]));
  for (const entry of entries) {
    const path = normalizePath(entry.path);
    for (const item of FOLDER_SUMMARY_TYPES) {
      if (item.matcher(path, path.split("/").pop() || path)) {
        counts[item.type] += 1;
      }
    }
  }
  return counts;
}

function mapLoadState(error) {
  const code = String(error?.code || error?.status || "").toLowerCase();
  if (code.includes("forbidden")) return "forbidden";
  if (code.includes("not_found")) return "not_found";
  if (code.includes("unauthorized") || code.includes("session")) return "unauthorized";
  if (code.includes("timeout")) return "timeout";
  if (code.includes("offline")) return "offline";
  return error ? "error" : "ready";
}

function readPreviewLines(content, limit = 220) {
  const text = String(content || "");
  const lines = text.replace(/\r\n/g, "\n").split("\n");
  const truncated = lines.length > limit;
  return {
    lines: truncated ? lines.slice(0, limit) : lines,
    truncated,
    lineCount: lines.length,
  };
}

function explorerKey(resource) {
  if (!resource) return "none";
  return `${resource.type}:${resource.workspaceId}:${resource.path || resource.id}`;
}

function ensureArray(value) {
  return Array.isArray(value) ? value : [];
}

function renderBadge(label, value, tone = "") {
  return h(
    "span",
    { className: tone ? `context-chip tone-${tone}` : "context-chip" },
    h("strong", null, label),
    h("span", null, value),
  );
}

function buttonClass(active) {
  return active ? "explorer-node active" : "explorer-node";
}

function ExplorerNode({
  node,
  depth,
  expandedPaths,
  selectedKey,
  onToggleExpand,
  onSelect,
  onContextMenu,
  filterText,
  visibleChildren,
  showActions = true,
}) {
  const hasChildren = Boolean(node.hasChildren || (node.children && node.children.length));
  const expanded = expandedPaths.has(node.id);
  const selected = selectedKey === node.id;
  const label = filterText && node.name.toLowerCase().includes(filterText.toLowerCase())
    ? h("mark", null, node.name)
    : node.name;

  const children = ensureArray(node.children).filter((child) => {
    if (!filterText) return true;
    const needle = filterText.toLowerCase();
    return [child.name, child.path, child.type, child.language, child.gitStatus]
      .filter(Boolean)
      .some((value) => String(value).toLowerCase().includes(needle));
  });

  return h(
    "div",
    { className: "explorer-tree-node-wrap" },
    h(
      "div",
      {
        role: "treeitem",
        "aria-expanded": hasChildren ? expanded : undefined,
        "aria-selected": selected,
        tabIndex: 0,
        className: buttonClass(selected),
        style: { paddingInlineStart: `${depth * 16 + 6}px` },
        onClick: () => onSelect(node),
        onKeyDown: (event) => {
          if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            onSelect(node);
          }
          if ((event.key === "ArrowRight" || event.key === "+") && hasChildren && !expanded) {
            event.preventDefault();
            onToggleExpand(node, true);
          }
          if ((event.key === "ArrowLeft" || event.key === "-") && hasChildren && expanded) {
            event.preventDefault();
            onToggleExpand(node, false);
          }
        },
        onContextMenu: (event) => {
          event.preventDefault();
          onContextMenu(node);
        },
      },
      h("span", { className: "explorer-node-disclosure", "aria-hidden": "true" }, hasChildren ? (expanded ? "▾" : "▸") : "•"),
      h("span", { className: "explorer-node-icon", "aria-hidden": "true" }, iconForResource(node)),
      h(
        "span",
        { className: "explorer-node-name" },
        label,
        node.childCount ? h("small", null, node.childCount) : null,
      ),
      node.gitStatus ? h("span", { className: `git-pill ${gitTone(node.gitStatus)}` }, node.gitStatus) : null,
      node.language ? h("span", { className: "language-pill" }, node.language) : null,
      showActions
        ? h(
            "button",
            {
              type: "button",
              className: "tree-node-actions",
              onClick: (event) => {
                event.stopPropagation();
                onContextMenu(node);
              },
              "aria-label": `Open actions for ${node.name}`,
            },
            "⋯",
          )
        : null,
    ),
    hasChildren && expanded && children.length
      ? h(
          "div",
          { role: "group" },
          children.map((child) =>
            h(ExplorerNode, {
              key: child.id,
              node: child,
              depth: depth + 1,
              expandedPaths,
              selectedKey,
              onToggleExpand,
              onSelect,
              onContextMenu,
              filterText,
              visibleChildren,
              showActions,
            }),
          ),
        )
      : null,
  );
}

function iconForResource(node) {
  switch (node.type) {
    case "organisation":
      return "🏢";
    case "workspace":
      return "🧭";
    case "product":
      return "◧";
    case "solution":
      return "⬡";
    case "project":
      return "■";
    case "application":
      return "app";
    case "service":
      return "svc";
    case "library":
      return "lib";
    case "package":
      return "pkg";
    case "repository":
      return "⇄";
    case "worktree":
      return "⤴";
    case "branch":
      return "⎇";
    case "folder":
      return "📁";
    case "test":
      return "🧪";
    case "documentation":
      return "📘";
    case "infrastructure":
      return "☁";
    case "evidence":
      return "⧉";
    case "dependency":
      return "∴";
    default:
      return "📄";
  }
}

function gitTone(status = "") {
  const value = String(status).toLowerCase();
  if (value.includes("modified")) return "modified";
  if (value.includes("added")) return "added";
  if (value.includes("deleted")) return "deleted";
  if (value.includes("renamed")) return "renamed";
  if (value.includes("untracked")) return "untracked";
  if (value.includes("ignored")) return "ignored";
  if (value.includes("conflict")) return "conflict";
  if (value.includes("staged")) return "staged";
  return "neutral";
}

function buildNodeSummary(node) {
  return [
    ["Type", node.type],
    ["Path", node.path || "Unavailable"],
    ["Repository", node.repositoryId || "Unavailable"],
    ["Branch", node.metadata?.branch || node.gitStatus || "Unavailable"],
    ["Project", node.projectId || "Unavailable"],
    ["Workspace", node.workspaceId || "Unavailable"],
    ["Owner", node.metadata?.owner || "Unavailable"],
    ["Language", node.language || "Unavailable"],
    ["Size", typeof node.sizeBytes === "number" ? `${node.sizeBytes.toLocaleString()} bytes` : "Unavailable"],
    ["Modified", node.modifiedAt || "Unavailable"],
    ["Classification", node.metadata?.classification || node.type],
    ["Git status", node.gitStatus || "Unavailable"],
    ["Coverage", node.metadata?.coverage ?? "Not indexed"],
  ];
}

function buildTraceabilityLinks(node, workspaceId) {
  const base = `/novacodepro/workspace/${encodeURIComponent(workspaceId)}/dashboard`;
  const links = [
    { label: "Workspace", route: base },
    { label: "Project", route: node.projectId ? `/novacodepro/projects/${encodeURIComponent(node.projectId)}` : "" },
    { label: "Repository", route: node.repositoryId ? `/novacodepro/development/workspaces/${encodeURIComponent(workspaceId)}/repository` : "" },
    { label: "Evidence", route: node.metadata?.evidenceId ? `/novacodepro/development/change-sets/${encodeURIComponent(node.metadata.evidenceId)}/evidence` : "" },
    { label: "Tests", route: node.type === "test" ? "/novacodepro/development/change-sets" : "" },
  ];
  return links.filter((item) => item.route);
}

function isSupportedTextFile(path, content) {
  const basename = normalizePath(path).split("/").pop() || "";
  const ext = fileExtension(path);
  if (SPECIAL_TEXT_FILENAMES.has(basename)) return true;
  if (SUPPORTED_TEXT_EXTENSIONS.has(ext)) return true;
  return typeof content === "string" && !/\x00/.test(content);
}

function resourceFromWorkspace(workspace, session) {
  return createExplorerResource({
    type: "workspace",
    name: workspace?.name || "Workspace",
    path: workspace?.home_route || "",
    workspaceId: workspace?.id || session?.workspace?.id || session?.workspace_id || "",
    organizationId: session?.organization?.id || session?.tenant?.id || session?.tenant_id || "",
    hasChildren: true,
    childCount: ensureArray(workspace?.projects).length || 0,
    metadata: {
      status: workspace?.status || "ACTIVE",
      homeRoute: workspace?.home_route || "",
      selectedEnvironment: workspace?.selected_environment || "development",
    },
  });
}

function createSummaryNode(type, name, workspaceId, organizationId, metadata = {}) {
  return createExplorerResource({
    type,
    name,
    path: metadata.path || name.toLowerCase().replace(/\s+/g, "-"),
    workspaceId,
    organizationId,
    hasChildren: false,
    childCount: metadata.childCount || 0,
    metadata,
  });
}

function buildRepositoryCategories(entries, workspaceId, organizationId, repositoryId) {
  const counts = countByCategory(entries);
  return FOLDER_SUMMARY_TYPES.map((category) =>
    createExplorerResource({
      type: category.type,
      name: category.label,
      path: category.type,
      workspaceId,
      organizationId,
      repositoryId,
      hasChildren: true,
      childCount: counts[category.type] || 0,
      metadata: { category: category.type, count: counts[category.type] || 0 },
    }),
  ).filter((node) => node.childCount > 0);
}

function filterTreeNodes(nodes, filterText) {
  const needle = String(filterText || "").trim().toLowerCase();
  if (!needle) return nodes;
  const filtered = [];
  for (const node of nodes) {
    const childMatches = node.children ? filterTreeNodes(node.children, needle) : [];
    const selfMatches = [node.name, node.path, node.type, node.language, node.gitStatus, node.metadata?.classification]
      .filter(Boolean)
      .some((value) => String(value).toLowerCase().includes(needle));
    if (selfMatches || childMatches.length) {
      filtered.push({ ...node, children: childMatches });
    }
  }
  return filtered;
}

function treeNodeCount(nodes) {
  let count = 0;
  for (const node of nodes) {
    count += 1;
    if (node.children) count += treeNodeCount(node.children);
  }
  return count;
}

function TreeSection({ title, subtitle, children, action }) {
  return h(
    "section",
    { className: "explorer-section" },
    h(
      "div",
      { className: "explorer-section-head" },
      h("div", null, h("strong", null, title), subtitle ? h("p", null, subtitle) : null),
      action ? h("div", { className: "explorer-section-action" }, action) : null,
    ),
    children,
  );
}

function TextRow({ label, value }) {
  return h(
    "div",
    { className: "explorer-meta-row" },
    h("span", null, label),
    h("strong", null, value || "Unavailable"),
  );
}

function PreviewBlock({ preview, onOpenInStudio }) {
  if (preview.state === "loading") {
    return h("div", { className: "explorer-state loading", role: "status", "aria-live": "polite" }, h("strong", null, "Loading file preview"), h("span", null, preview.message || "Reading file content."));
  }
  if (preview.state === "forbidden") {
    return h("div", { className: "explorer-state forbidden", role: "alert" }, h("strong", null, "Permission denied"), h("span", null, preview.message || "You are not authorised to preview this resource."));
  }
  if (preview.state === "not_found") {
    return h("div", { className: "explorer-state not-found", role: "alert" }, h("strong", null, "Resource not found"), h("span", null, preview.message || "The selected resource is unavailable."));
  }
  if (preview.state === "binary") {
    return h("div", { className: "explorer-state unsupported", role: "status" }, h("strong", null, "Binary file"), h("span", null, "Binary content is not rendered in the explorer."));
  }
  if (preview.state === "unsupported") {
    return h(
      "div",
      { className: "explorer-state unsupported", role: "status" },
      h("strong", null, "Unsupported preview"),
      h("span", null, "Open-in-editor is unavailable until NCP-STUDIO-003."),
      h(
        "button",
        { type: "button", className: "toolbar-chip", onClick: onOpenInStudio },
        "Open in editor (unavailable)",
      ),
    );
  }
  if (preview.state === "error") {
    return h("div", { className: "explorer-state error", role: "alert" }, h("strong", null, "Preview error"), h("span", null, preview.message || "Unable to load preview."));
  }

  const lines = preview.lines || [];
  return h(
    "div",
    { className: "explorer-preview" },
    h(
      "div",
      { className: "explorer-preview-meta" },
      h("span", null, preview.language || "Plain text"),
      h("span", null, preview.encoding || "utf-8"),
      h("span", null, preview.sizeLabel || "Unavailable"),
      preview.truncated ? h("span", { className: "warning-pill" }, "Truncated") : null,
    ),
    h(
      "pre",
      { className: "explorer-code", role: "region", "aria-label": "File preview" },
      lines.map((line, index) =>
        h(
          "div",
          { key: `${index}-${line.slice(0, 12)}`, className: "explorer-code-line" },
          h("span", { className: "explorer-code-line-number" }, String(index + 1).padStart(3, " ")),
          h("span", { className: "explorer-code-line-text" }, line || "\u00A0"),
        ),
      ),
    ),
    preview.truncated ? h("p", { className: "studio-note" }, "Preview truncated for size; select the file in the full editor when available.") : null,
  );
}

function buildExplorerWorkspaceTree({
  session,
  selectedWorkspace,
  workspaces,
  workspaceProjects,
  workspaceFavorites,
  recentResources,
  openEditors,
  repositoryRootNode,
  repositoryCategories,
  repositoryStatus,
  selectedWorkspaceId,
}) {
  const organizationId = session?.organization?.id || session?.tenant?.id || session?.tenant_id || "";
  const workspaceNodes = ensureArray(workspaces).map((workspace) =>
    createExplorerResource({
      type: "workspace",
      name: workspace.name,
      path: workspace.id,
      workspaceId: workspace.id,
      organizationId,
      hasChildren: true,
      childCount: ensureArray(workspaceProjects).length,
      metadata: {
        status: workspace.status || "ACTIVE",
        homeRoute: workspace.home_route || "",
        selected: workspace.id === selectedWorkspaceId,
      },
    }),
  );

  const projectNodes = ensureArray(workspaceProjects).map((project) =>
    createExplorerResource({
      type: "project",
      name: project.name,
      path: project.id,
      workspaceId: selectedWorkspaceId,
      organizationId,
      projectId: project.id,
      hasChildren: true,
      childCount: ensureArray(project.work_items).length || ensureArray(project.members).length || 0,
      metadata: {
        status: project.status || "DRAFT",
        owner: project.owner_id || project.created_by || "Unavailable",
        repository: project.repository || "Not indexed",
        branch: project.branch || repositoryStatus?.branch || "Not indexed",
        traceability: "project",
      },
    }),
  );

  const solutionNode = createExplorerResource({
    type: "solution",
    name: selectedWorkspace?.name ? `${selectedWorkspace.name} solution` : "Workspace solution",
    path: `${selectedWorkspaceId || "workspace"}/solution`,
    workspaceId: selectedWorkspaceId,
    organizationId,
    hasChildren: true,
    childCount: projectNodes.length,
    metadata: {
      status: selectedWorkspace?.status || "ACTIVE",
      selectedWorkspace: selectedWorkspace?.name || "Workspace",
    },
  });

  const productNode = createExplorerResource({
    type: "product",
    name: selectedWorkspace?.name ? `${selectedWorkspace.name} product` : "Workspace product",
    path: `${selectedWorkspaceId || "workspace"}/product`,
    workspaceId: selectedWorkspaceId,
    organizationId,
    hasChildren: true,
    childCount: 1,
    metadata: { status: selectedWorkspace?.status || "ACTIVE" },
  });

  const repoRoot = repositoryRootNode
    ? createExplorerResource({
        ...repositoryRootNode,
        type: "repository",
        name: repositoryStatus?.branch ? `Repository (${repositoryStatus.branch})` : "Repository",
        repositoryId: repositoryStatus?.root || selectedWorkspaceId,
        metadata: {
          ...(repositoryRootNode.metadata || {}),
          branch: repositoryStatus?.branch || "Unavailable",
          headSha: repositoryStatus?.head_sha || "Unavailable",
          dirty: String(repositoryStatus?.dirty ?? false),
          root: repositoryStatus?.root || "Unavailable",
        },
      })
    : createExplorerResource({
        type: "repository",
        name: "Repository",
        path: ".",
        workspaceId: selectedWorkspaceId,
        organizationId,
        repositoryId: repositoryStatus?.root || selectedWorkspaceId,
        hasChildren: true,
        childCount: 0,
        metadata: {
          branch: repositoryStatus?.branch || "Unavailable",
          headSha: repositoryStatus?.head_sha || "Unavailable",
          dirty: String(repositoryStatus?.dirty ?? false),
          root: repositoryStatus?.root || "Unavailable",
        },
      });

  const branchNode = createExplorerResource({
    type: "branch",
    name: repositoryStatus?.branch || "main",
    path: repositoryStatus?.branch || "main",
    workspaceId: selectedWorkspaceId,
    organizationId,
    repositoryId: repoRoot.repositoryId,
    metadata: { headSha: repositoryStatus?.head_sha || "Unavailable", dirty: String(repositoryStatus?.dirty ?? false) },
  });

  const worktreeNode = createExplorerResource({
    type: "worktree",
    name: "Active worktree",
    path: repositoryStatus?.root || ".",
    workspaceId: selectedWorkspaceId,
    organizationId,
    repositoryId: repoRoot.repositoryId,
    metadata: { root: repositoryStatus?.root || "Unavailable" },
  });

  const repositoryChildren = [branchNode, worktreeNode, ...repositoryCategories, repoRoot];

  const root = createExplorerResource({
    type: "organisation",
    name: session?.organization?.name || "NovaTech",
    path: session?.organization?.id || session?.tenant?.id || "organisation",
    workspaceId: selectedWorkspaceId,
    organizationId,
    hasChildren: true,
    childCount: workspaceNodes.length,
    metadata: { classification: "tenant-root" },
  });

  return [
    {
      ...root,
      children: [
        {
          ...createExplorerResource({
            type: "workspace",
            name: selectedWorkspace?.name || "Workspace",
            path: selectedWorkspaceId,
            workspaceId: selectedWorkspaceId,
            organizationId,
            hasChildren: true,
            childCount: projectNodes.length + repositoryChildren.length,
            metadata: {
              status: selectedWorkspace?.status || "ACTIVE",
              defaultBranch: selectedWorkspace?.default_branch || "main",
              homeRoute: selectedWorkspace?.home_route || "",
            },
          }),
          children: [
            {
              ...solutionNode,
              children: [
                ...projectNodes.map((project) => ({
                  ...project,
                  children: [
                    createExplorerResource({
                      type: "repository",
                      name: project.metadata.repository || "Repository",
                      path: `${project.path || project.id}/repository`,
                      workspaceId: selectedWorkspaceId,
                      organizationId,
                      projectId: project.projectId,
                      repositoryId: project.metadata.repository || repoRoot.repositoryId,
                      hasChildren: true,
                      childCount: repoRoot.childCount,
                      metadata: {
                        branch: project.metadata.branch || repoRoot.metadata.branch || "main",
                        headSha: repoRoot.metadata.headSha || "Unavailable",
                        status: project.metadata.status || "ACTIVE",
                      },
                    }),
                  ],
                })),
              ],
            },
            createExplorerResource({
              type: "repository",
              name: "Repository overview",
              path: `${selectedWorkspaceId || "workspace"}/repository`,
              workspaceId: selectedWorkspaceId,
              organizationId,
              repositoryId: repoRoot.repositoryId,
              hasChildren: true,
              childCount: repositoryChildren.length,
              metadata: { branch: repositoryStatus?.branch || "main", headSha: repositoryStatus?.head_sha || "Unavailable" },
            }),
            ...repositoryChildren,
            createExplorerResource({
              type: "dependency",
              name: "Dependencies",
              path: `${selectedWorkspaceId || "workspace"}/dependencies`,
              workspaceId: selectedWorkspaceId,
              organizationId,
              hasChildren: true,
              childCount: repositoryCategories.filter((node) => node.type === "package").length,
              metadata: { status: "Indexed from repository manifest files" },
            }),
            createExplorerResource({
              type: "test",
              name: "Tests",
              path: `${selectedWorkspaceId || "workspace"}/tests`,
              workspaceId: selectedWorkspaceId,
              organizationId,
              hasChildren: true,
              childCount: repositoryCategories.filter((node) => node.type === "test").length,
              metadata: { status: "Indexed from repository files" },
            }),
            createExplorerResource({
              type: "documentation",
              name: "Documentation",
              path: `${selectedWorkspaceId || "workspace"}/docs`,
              workspaceId: selectedWorkspaceId,
              organizationId,
              hasChildren: true,
              childCount: repositoryCategories.filter((node) => node.type === "documentation").length,
              metadata: { status: "Indexed from repository files" },
            }),
            createExplorerResource({
              type: "infrastructure",
              name: "Infrastructure",
              path: `${selectedWorkspaceId || "workspace"}/infra`,
              workspaceId: selectedWorkspaceId,
              organizationId,
              hasChildren: true,
              childCount: repositoryCategories.filter((node) => node.type === "infrastructure").length,
              metadata: { status: "Indexed from repository files" },
            }),
            createExplorerResource({
              type: "evidence",
              name: "Evidence",
              path: `${selectedWorkspaceId || "workspace"}/evidence`,
              workspaceId: selectedWorkspaceId,
              organizationId,
              hasChildren: true,
              childCount: repositoryCategories.filter((node) => node.type === "evidence").length,
              metadata: { status: "Indexed from repository files" },
            }),
            createExplorerResource({
              type: "package",
              name: "Packages",
              path: `${selectedWorkspaceId || "workspace"}/packages`,
              workspaceId: selectedWorkspaceId,
              organizationId,
              hasChildren: true,
              childCount: repositoryCategories.filter((node) => node.type === "package").length,
              metadata: { status: "Indexed from repository files" },
            }),
            ...workspaceNodes,
            ...projectNodes,
            ...ensureArray(openEditors).map((item) =>
              createExplorerResource({
                type: "file",
                name: item.name,
                path: item.path,
                workspaceId: selectedWorkspaceId,
                organizationId,
                repositoryId: repoRoot.repositoryId,
                projectId: item.projectId || "",
                language: item.language || languageFromPath(item.path),
                gitStatus: item.gitStatus || "Preview",
                sizeBytes: item.sizeBytes,
                metadata: { pinned: Boolean(item.pinned), source: "open-editors" },
              }),
            ),
            ...ensureArray(workspaceFavorites).map((item) =>
              createExplorerResource({
                type: "evidence",
                name: item.label || item.name || "Favorite",
                path: item.route || item.path || item.id,
                workspaceId: selectedWorkspaceId,
                organizationId,
                repositoryId: repoRoot.repositoryId,
                metadata: { route: item.route || "", favoriteId: item.id, source: "workspace-favorite" },
              }),
            ),
            ...ensureArray(recentResources).map((item) =>
              createExplorerResource({
                type: item.type || "file",
                name: item.name,
                path: item.path,
                workspaceId: selectedWorkspaceId,
                organizationId,
                repositoryId: repoRoot.repositoryId,
                projectId: item.projectId || "",
                language: item.language || languageFromPath(item.path),
                gitStatus: item.gitStatus || "Recent",
                sizeBytes: item.sizeBytes,
                metadata: { source: "recent" },
              }),
            ),
          ],
        },
      ],
    },
  ];
}

function explorerActionMenu(node, { isFavourite, canLoadRepository, onAddFavourite, onRemoveFavourite, onOpenFile, onOpenResource, onRefresh, onCopyPath, onCopyRepositoryPath, onOpenDevelopmentStudio, onClearRecent }) {
  const common = [
    { id: "open", label: "Open", enabled: node.type === "file" || node.type === "folder", action: () => onOpenResource(node) },
    { id: "preview", label: "Preview", enabled: node.type === "file", action: () => onOpenFile(node) },
    { id: "refresh", label: "Refresh", enabled: true, action: () => onRefresh(node) },
    { id: "copy-path", label: "Copy relative path", enabled: Boolean(node.path), action: () => onCopyPath(node) },
    { id: "copy-repo-path", label: "Copy repository path", enabled: Boolean(node.path), action: () => onCopyRepositoryPath(node) },
    { id: "properties", label: "View properties", enabled: true, action: () => onOpenResource(node) },
    { id: "trace", label: "Reveal in traceability", enabled: true, action: () => onOpenResource(node) },
    { id: "architecture", label: "Reveal in architecture", enabled: true, action: () => onOpenResource(node) },
    { id: "history", label: "View history", enabled: true, action: () => onOpenResource(node) },
    { id: "development", label: "Open governed mutation workflow", enabled: canLoadRepository && node.type !== "workspace", action: () => onOpenDevelopmentStudio(node) },
    { id: "add-favorite", label: "Add to favourites", enabled: !isFavourite, action: () => onAddFavourite(node) },
    { id: "remove-favorite", label: "Remove from favourites", enabled: isFavourite, action: () => onRemoveFavourite(node) },
    { id: "clear-recent", label: "Clear recent history", enabled: node.type === "workspace", action: () => onClearRecent() },
  ];
  if (node.type === "file") {
    common.push({ id: "download", label: "Download", enabled: false, reason: "Download is not enabled in this release." });
  } else {
    common.push({ id: "new-file", label: "New file", enabled: false, reason: "Create file is governed by the development workflow." });
    common.push({ id: "new-folder", label: "New folder", enabled: false, reason: "Create folder is governed by the development workflow." });
    common.push({ id: "rename", label: "Rename", enabled: false, reason: "Rename is governed by the development workflow." });
    common.push({ id: "move", label: "Move", enabled: false, reason: "Move is governed by the development workflow." });
    common.push({ id: "copy", label: "Copy", enabled: false, reason: "Copy is governed by the development workflow." });
    common.push({ id: "delete", label: "Delete", enabled: false, reason: "Delete is governed by the development workflow." });
    common.push({ id: "duplicate", label: "Duplicate", enabled: false, reason: "Duplicate is governed by the development workflow." });
  }
  return common;
}

function ResourceMenu({ node, menu, onClose }) {
  if (!node || !menu?.length) return null;
  return h(
    "div",
    { className: "explorer-context-menu", role: "menu", "aria-label": `Actions for ${node.name}` },
    menu.map((item) =>
      h(
        "button",
        {
          key: item.id,
          type: "button",
          role: "menuitem",
          className: item.enabled ? "explorer-context-menu-item" : "explorer-context-menu-item disabled",
          disabled: !item.enabled,
          title: item.reason || "",
          onClick: () => {
            if (item.enabled) {
              item.action?.();
              onClose?.();
            }
          },
        },
        h("strong", null, item.label),
        h("span", null, item.reason || (item.enabled ? "Available" : "Unavailable")),
      ),
    ),
  );
}

function ExplorerView({
  session,
  environment,
  activeRole,
  activeProject,
  workspaces,
  selectedWorkspaceId,
  selectedWorkspace,
  workspaceProjects,
  workspaceFavorites,
  recentResources,
  openEditors,
  selectedResource,
  repositoryStatus,
  repositoryEntries,
  repositoryCategories,
  repositoryTreeLoaded,
  searchQuery,
  searchResults,
  searchState,
  preview,
  expandedPaths,
  loadState,
  loadError,
  filterText,
  onSelectWorkspace,
  onRefreshWorkspace,
  onRefreshRepository,
  onCollapseAll,
  onToggleExpand,
  onSelectNode,
  onOpenFilePreview,
  onOpenResource,
  onAddFavorite,
  onRemoveFavorite,
  onCopyPath,
  onCopyRepositoryPath,
  onOpenDevelopmentStudio,
  onClearRecent,
  onPinEditor,
  onCloseEditor,
  onCloseAllEditors,
  onSelectOpenEditor,
  onFilterTextChange,
  onSearchQueryChange,
  onSearchSubmit,
  onClearSearch,
  onOpenContextMenu,
  onCloseContextMenu,
  contextMenuNode,
  contextMenuItems,
}) {
  const tree = buildExplorerWorkspaceTree({
    session,
    selectedWorkspace,
    workspaces,
    workspaceProjects,
    workspaceFavorites,
    recentResources,
    openEditors,
    repositoryRootNode: repositoryTreeLoaded
      ? createExplorerResource({
          type: "repository",
          name: repositoryStatus?.branch ? `Repository (${repositoryStatus.branch})` : "Repository",
          path: repositoryStatus?.root || ".",
          workspaceId: selectedWorkspaceId,
          organizationId: session?.organization?.id || session?.tenant?.id || session?.tenant_id || "",
          repositoryId: repositoryStatus?.root || selectedWorkspaceId,
          hasChildren: true,
          childCount: repositoryEntries.length,
          metadata: { branch: repositoryStatus?.branch || "main", headSha: repositoryStatus?.head_sha || "Unavailable", root: repositoryStatus?.root || "." },
        })
      : null,
    repositoryCategories,
    repositoryStatus,
    selectedWorkspaceId,
  });
  const explorerRoots = filterTreeNodes(tree, filterText);
  const visibleCount = treeNodeCount(explorerRoots);

  const selectedSummary = selectedResource ? buildNodeSummary(selectedResource) : [];
  const traceLinks = selectedResource ? buildTraceabilityLinks(selectedResource, selectedWorkspaceId) : [];

  const workspaceContext = [
    renderBadge("Organisation", session?.organization?.name || "NovaTech"),
    renderBadge("Workspace", selectedWorkspace?.name || "Unavailable"),
    renderBadge("Project", activeProject?.name || "Unavailable"),
    renderBadge("Environment", environment || "Unavailable"),
    renderBadge("Repository", repositoryStatus?.root || "Not indexed"),
    renderBadge("Branch", repositoryStatus?.branch || "Not indexed"),
    renderBadge("Git", repositoryStatus?.dirty ? "Dirty" : "Clean", repositoryStatus?.dirty ? "warning" : "success"),
  ];

  return h(
    "section",
    { className: "studio-explorer", "aria-label": "Explorer workbench" },
    h(
      "header",
      { className: "explorer-header" },
      h(
        "div",
        null,
        h("p", { className: "eyebrow" }, "Explorer"),
        h("h1", null, "Governed solution, project, repository and file explorer"),
        h("p", { className: "studio-note" }, "Real workspace and repository data with governed mutation paths, traceability, and safe previews."),
      ),
      h(
        "div",
        { className: "explorer-header-actions" },
        h("button", { type: "button", className: "toolbar-chip", onClick: onRefreshWorkspace }, "Refresh workspace"),
        h("button", { type: "button", className: "toolbar-chip", onClick: onRefreshRepository, disabled: !selectedWorkspaceId }, "Refresh repository"),
        h("button", { type: "button", className: "toolbar-chip", onClick: onCollapseAll }, "Collapse all"),
        h(
          "button",
          {
            type: "button",
            className: "toolbar-chip",
            onClick: () => onOpenDevelopmentStudio(selectedResource || selectedWorkspace),
            disabled: !selectedWorkspaceId,
            title: "Open governed mutation workflow in Development Studio",
          },
          "New resource",
        ),
      ),
    ),
    h("div", { className: "explorer-context-row" }, ...workspaceContext),
    loadState !== "ready" && loadError
      ? h(
          "div",
          { className: `explorer-state ${loadState || "error"}`, role: "status", "aria-live": "polite" },
          h("strong", null, loadState === "forbidden" ? "Authorisation denied" : loadState === "not_found" ? "Resource not found" : "Explorer unavailable"),
          h("span", null, loadError.message || loadError.code || "Unable to load explorer data."),
        )
      : null,
    h(
      "div",
      { className: "studio-explorer-grid" },
      h(
        "aside",
        { className: "explorer-sidebar" },
        h(
          TreeSection,
          {
            title: "Workspace tree",
            subtitle: `${ensureArray(workspaces).length} workspaces · ${ensureArray(workspaceProjects).length} projects`,
            action: h(
              "label",
              { className: "explorer-select" },
              h("span", null, "Workspace"),
              h(
                "select",
                {
                  value: selectedWorkspaceId,
                  onChange: (event) => onSelectWorkspace(event.target.value),
                  "aria-label": "Select workspace",
                },
                ensureArray(workspaces).map((workspace) => h("option", { key: workspace.id, value: workspace.id }, workspace.name)),
              ),
            ),
          },
          h(
            "div",
            { role: "tree", "aria-label": "Workspace tree" },
            explorerRoots
              .filter((node) => node.type === "organisation")
              .map((root) =>
                h(ExplorerNode, {
                  key: root.id,
                  node: root,
                  depth: 0,
                  expandedPaths,
                  selectedKey: explorerKey(selectedResource),
                  onToggleExpand,
                  onSelect: onSelectNode,
                  onContextMenu: onOpenContextMenu,
                  filterText,
                  visibleChildren: explorerRoots,
                }),
              ),
          ),
        ),
        h(
          TreeSection,
          {
            title: "Repository tree",
            subtitle: repositoryTreeLoaded ? `${repositoryEntries.length} indexed files` : "Repository tree loads on demand",
            action: h(
              "button",
              {
                type: "button",
                className: "toolbar-chip",
                onClick: onRefreshRepository,
                disabled: !selectedWorkspaceId,
                title: "Load repository tree for the selected workspace",
              },
              repositoryTreeLoaded ? "Reload tree" : "Load tree",
            ),
          },
          repositoryTreeLoaded
            ? h(
                "div",
                { role: "tree", "aria-label": "Repository tree" },
                explorerRoots
                  .filter((node) => node.type !== "organisation")
                  .map((root) =>
                    h(ExplorerNode, {
                      key: root.id,
                      node: root,
                      depth: 0,
                      expandedPaths,
                      selectedKey: explorerKey(selectedResource),
                      onToggleExpand,
                      onSelect: onSelectNode,
                      onContextMenu: onOpenContextMenu,
                      filterText,
                      visibleChildren: explorerRoots,
                    }),
                  ),
              )
            : h("div", { className: "explorer-empty" }, h("strong", null, "Repository root is not loaded"), h("p", null, "Expand the repository node or refresh the tree to fetch a governed snapshot.")),
        ),
        h(
          TreeSection,
          {
            title: "Open editors",
            subtitle: `${ensureArray(openEditors).length} tracked previews`,
            action: h(
              "button",
              { type: "button", className: "toolbar-chip", onClick: onCloseAllEditors, disabled: !ensureArray(openEditors).length },
              "Close all",
            ),
          },
          ensureArray(openEditors).length
            ? h(
                "div",
                { className: "stack" },
                openEditors.map((editor) =>
                  h(
                    "div",
                    { className: editor.id === selectedResource?.id ? "stack-item active" : "stack-item", key: editor.id },
                    h("strong", null, editor.name),
                    h("span", null, `${editor.path || "Unavailable"} · ${editor.pinned ? "Pinned" : "Preview"}`),
                    h(
                      "div",
                      { className: "inline-actions" },
                      h("button", { type: "button", className: "toolbar-chip", onClick: () => onSelectOpenEditor(editor) }, "Select"),
                      h("button", { type: "button", className: "toolbar-chip", onClick: () => onPinEditor(editor) }, editor.pinned ? "Unpin" : "Pin"),
                      h("button", { type: "button", className: "toolbar-chip", onClick: () => onCloseEditor(editor) }, "Close"),
                    ),
                  ),
                ),
              )
            : h("p", { className: "explorer-empty" }, "No open editors yet."),
        ),
        h(
          TreeSection,
          {
            title: "Favourites",
            subtitle: `${ensureArray(workspaceFavorites).length} saved`,
            action: h(
              "button",
              { type: "button", className: "toolbar-chip", onClick: onClearRecent },
              "Clear recent",
            ),
          },
          ensureArray(workspaceFavorites).length
            ? h(
                "div",
                { className: "stack" },
                workspaceFavorites.map((favorite) =>
                  h(
                    "button",
                    {
                      type: "button",
                      key: favorite.id,
                      className: "stack-item stack-link",
                      onClick: () => onOpenResource({ ...selectedResource, path: favorite.route || favorite.path || "", type: "evidence", metadata: { favoriteId: favorite.id } }),
                    },
                    h("strong", null, favorite.label || favorite.name || "Favorite"),
                    h("span", null, favorite.route || favorite.path || "Unavailable"),
                  ),
                ),
              )
            : h("p", { className: "explorer-empty" }, "No favourites yet."),
        ),
        h(
          TreeSection,
          { title: "Recent resources", subtitle: `${ensureArray(recentResources).length} tracked` },
          ensureArray(recentResources).length
            ? h(
                "div",
                { className: "stack" },
                recentResources.map((item) =>
                  h(
                    "button",
                    { type: "button", key: item.id || `${item.path}-${item.name}`, className: "stack-item stack-link", onClick: () => onSelectNode(item) },
                    h("strong", null, item.name),
                    h("span", null, item.path || "Unavailable"),
                  ),
                ),
              )
            : h("p", { className: "explorer-empty" }, "No recent resources."),
        ),
      ),
      h(
        "main",
        { className: "explorer-main" },
        h(
          "section",
          { className: "explorer-center-card" },
          selectedResource
            ? h(
                "div",
                null,
                h("p", { className: "section-label" }, "Selected resource"),
                h("h2", null, selectedResource.name),
                h("p", { className: "studio-note" }, selectedResource.path || "No path available."),
                selectedResource.type === "file"
                  ? h(PreviewBlock, {
                      preview,
                      onOpenInStudio: () => onOpenDevelopmentStudio(selectedResource),
                    })
                  : h(
                      "div",
                      { className: "explorer-summary" },
                      selectedResource.type === "repository"
                        ? h(
                            "div",
                            { className: "stack-item" },
                            h("strong", null, "Repository overview"),
                            h("span", null, `Branch ${repositoryStatus?.branch || "Unavailable"} · HEAD ${repositoryStatus?.head_sha || "Unavailable"} · Dirty ${String(repositoryStatus?.dirty ?? false)}`),
                          )
                        : null,
                      selectedResource.type === "folder"
                        ? h(
                            "div",
                            { className: "stack-item" },
                            h("strong", null, "Directory summary"),
                            h("span", null, `Children ${selectedResource.childCount || selectedResource.metadata?.childCount || 0}`),
                          )
                        : null,
                      selectedResource.type === "project"
                        ? h(
                            "div",
                            { className: "stack-item" },
                            h("strong", null, "Project overview"),
                            h("span", null, `${selectedResource.metadata?.status || "ACTIVE"} · ${selectedResource.metadata?.branch || "main"}`),
                          )
                        : null,
                      selectedResource.type === "solution"
                        ? h(
                            "div",
                            { className: "stack-item" },
                            h("strong", null, "Solution overview"),
                            h("span", null, `${selectedResource.childCount || 0} projects linked`),
                          )
                        : null,
                      selectedResource.type === "workspace"
                        ? h(
                            "div",
                            { className: "stack-item" },
                            h("strong", null, "Workspace overview"),
                            h("span", null, `${selectedWorkspace?.status || "ACTIVE"} · ${selectedWorkspace?.home_route || "No home route"}`),
                          )
                        : null,
                      h(
                        "div",
                        { className: "center-actions" },
                        h("button", { type: "button", className: "toolbar-chip", onClick: () => onOpenResource(selectedResource) }, "View properties"),
                        h("button", { type: "button", className: "toolbar-chip", onClick: () => onOpenDevelopmentStudio(selectedResource) }, "Open governed workflow"),
                        h("button", { type: "button", className: "toolbar-chip", onClick: () => onAddFavorite(selectedResource), disabled: false }, "Add to favourites"),
                      ),
                    ),
              )
            : h(
                "div",
                { className: "explorer-empty-state" },
                h("p", { className: "section-label" }, "Explorer welcome"),
                h("h2", null, "Select a workspace, project, repository, folder, or file"),
                h("p", { className: "studio-note" }, "The explorer uses governed workspace and repository APIs to browse real data, inspect metadata, and preview text files."),
              ),
        ),
        h(
          "section",
          { className: "explorer-search-card" },
          h(
            "div",
            { className: "explorer-search-bar" },
            h("label", { className: "explorer-search-field" }, h("span", null, "Filter tree"), h("input", { type: "search", value: filterText, onChange: (event) => onFilterTextChange(event.target.value), placeholder: "Name, path, type, language, status" })),
            h("label", { className: "explorer-search-field" }, h("span", null, "Repository search"), h("input", { type: "search", value: searchQuery, onChange: (event) => onSearchQueryChange(event.target.value), placeholder: "Search repository content" })),
            h(
              "div",
              { className: "explorer-search-actions" },
              h("button", { type: "button", className: "toolbar-chip", onClick: onSearchSubmit, disabled: !searchQuery.trim() }, "Search"),
              h("button", { type: "button", className: "toolbar-chip", onClick: onClearSearch }, "Clear"),
            ),
          ),
          searchState === "loading"
            ? h("div", { className: "explorer-state loading" }, h("strong", null, "Searching repository"), h("span", null, "Using the backend repository search index."))
            : null,
          searchState === "error"
            ? h("div", { className: "explorer-state error", role: "alert" }, h("strong", null, "Search failed"), h("span", null, "The repository search request could not be completed."))
            : null,
          h(
            "div",
            { className: "explorer-search-results" },
            searchResults.length
              ? searchResults.map((result) =>
                  h(
                    "button",
                    {
                      type: "button",
                      key: result.path,
                      className: "stack-item stack-link",
                      onClick: () => onOpenFilePreview({ path: result.path, name: result.path.split("/").pop(), type: "file", workspaceId: selectedWorkspaceId, organizationId: session?.organization?.id || "" }),
                    },
                    h("strong", null, result.path),
                    h("span", null, result.snippet || "Match"),
                  ),
                )
              : h("p", { className: "explorer-empty" }, searchQuery.trim() ? "No search matches." : "Search the repository without recursively downloading file contents."),
          ),
        ),
      ),
      h(
        "aside",
        { className: "explorer-inspector" },
        h(
          TreeSection,
          { title: "Context inspector", subtitle: "Resource metadata, traceability, and governance" },
          selectedResource
            ? h(
                "div",
                { className: "inspector-stack" },
                ...selectedSummary.map(([label, value]) => h(TextRow, { key: label, label, value })),
                h(
                  "div",
                  { className: "inspector-links" },
                  h("strong", null, "Traceability links"),
                  traceLinks.length
                    ? traceLinks.map((item) =>
                        h(
                          "a",
                          { key: item.label, href: item.route, className: "stack-link" },
                          h("strong", null, item.label),
                          h("span", null, item.route),
                        ),
                      )
                    : h("p", { className: "explorer-empty" }, "Not indexed"),
                ),
                h(
                  "div",
                  { className: "inspector-links" },
                  h("strong", null, "Security findings"),
                  h("p", { className: "explorer-empty" }, selectedResource.metadata?.security || "Not indexed"),
                ),
                h(
                  "div",
                  { className: "inspector-links" },
                  h("strong", null, "Requirement coverage"),
                  h("p", { className: "explorer-empty" }, selectedResource.metadata?.requirementCoverage || "Not indexed"),
                ),
                h(
                  "div",
                  { className: "inspector-links" },
                  h("strong", null, "Test coverage"),
                  h("p", { className: "explorer-empty" }, selectedResource.metadata?.testCoverage || "Not indexed"),
                ),
                h(
                  "div",
                  { className: "inspector-links" },
                  h("strong", null, "Deployment relationships"),
                  h("p", { className: "explorer-empty" }, selectedResource.metadata?.deployment || "Not indexed"),
                ),
                h(
                  "div",
                  { className: "inspector-links" },
                  h("strong", null, "Audit history"),
                  h("p", { className: "explorer-empty" }, selectedResource.metadata?.audit || "Not indexed"),
                ),
              )
            : h("p", { className: "explorer-empty" }, "Select a resource to inspect its metadata."),
        ),
      ),
    ),
    contextMenuNode
      ? h(ResourceMenu, {
          node: contextMenuNode,
          menu: contextMenuItems,
          onClose: onCloseContextMenu,
        })
      : null,
    h(
      "footer",
      { className: "explorer-footer" },
      h("span", null, `Visible nodes ${visibleCount}`),
      h("span", null, repositoryTreeLoaded ? `Repository indexed · ${repositoryEntries.length} files` : "Repository tree not yet loaded"),
      h("span", null, `Workspace favourites ${ensureArray(workspaceFavorites).length}`),
      h("span", null, `Open editors ${ensureArray(openEditors).length}`),
    ),
  );
}

export function StudioExplorer({
  session,
  environment = "Development",
  activeRole = {},
  activeProject = null,
  baseUrl = "",
  seedData = null,
  navigate = () => {},
  onOpenPalette = () => {},
  onFocusNav = () => {},
}) {
  const ncp003 = useMemo(() => createNovaCodeProNcp003Api({ baseUrl, fetchImpl: globalThis.fetch }), [baseUrl]);
  const ncp007 = useMemo(() => createNovaCodeProNcp007Api({ baseUrl, fetchImpl: globalThis.fetch }), [baseUrl]);
  const workspaceIdFallback = session?.workspace?.id || session?.workspace_id || "";
  const [loadState, setLoadState] = useState(seedData ? "ready" : "loading");
  const [loadError, setLoadError] = useState(null);
  const [workspaces, setWorkspaces] = useState(seedData?.workspaces || []);
  const [selectedWorkspaceId, setSelectedWorkspaceId] = useState(seedData?.selectedWorkspaceId || workspaceIdFallback);
  const [selectedWorkspace, setSelectedWorkspace] = useState(seedData?.selectedWorkspace || null);
  const [workspaceProjects, setWorkspaceProjects] = useState(seedData?.workspaceProjects || []);
  const [workspaceFavorites, setWorkspaceFavorites] = useState(seedData?.workspaceFavorites || []);
  const [recentResources, setRecentResources] = useState(seedData?.recentResources || []);
  const [openEditors, setOpenEditors] = useState(seedData?.openEditors || []);
  const [repositoryStatus, setRepositoryStatus] = useState(seedData?.repositoryStatus || null);
  const [repositoryEntries, setRepositoryEntries] = useState(seedData?.repositoryEntries || []);
  const [repositoryTreeLoaded, setRepositoryTreeLoaded] = useState(Boolean(seedData?.repositoryTreeLoaded));
  const [selectedResource, setSelectedResource] = useState(seedData?.selectedResource || null);
  const [preview, setPreview] = useState(seedData?.preview || { state: "idle" });
  const [searchQuery, setSearchQuery] = useState(seedData?.searchQuery || "");
  const [searchResults, setSearchResults] = useState(seedData?.searchResults || []);
  const [searchState, setSearchState] = useState("idle");
  const [filterText, setFilterText] = useState(seedData?.filterText || "");
  const [expandedPaths, setExpandedPaths] = useState(() => {
    const stored = loadStoredValue(session, selectedWorkspaceId || workspaceIdFallback, "expanded", []);
    return new Set(Array.isArray(stored) ? stored : []);
  });
  const [contextMenuNode, setContextMenuNode] = useState(null);
  const [contextMenuItems, setContextMenuItems] = useState([]);
  const abortRef = useRef(null);

  const repositoryCategories = useMemo(
    () => (repositoryEntries.length ? buildRepositoryCategories(repositoryEntries, selectedWorkspaceId, session?.organization?.id || session?.tenant?.id || "", repositoryStatus?.root || selectedWorkspaceId) : []),
    [repositoryEntries, repositoryStatus?.root, selectedWorkspaceId, session?.organization?.id, session?.tenant?.id],
  );

  useEffect(() => {
    storeValue(session, selectedWorkspaceId || workspaceIdFallback, "expanded", [...expandedPaths]);
  }, [expandedPaths, selectedWorkspaceId, session, workspaceIdFallback]);

  useEffect(() => {
    if (seedData) return undefined;
    let cancelled = false;
    async function loadWorkspaceData() {
      setLoadState("loading");
      setLoadError(null);
      try {
        const workspaceList = await ncp003.listWorkspaces();
        if (cancelled) return;
        setWorkspaces(workspaceList);
        const nextWorkspaceId = selectedWorkspaceId || workspaceIdFallback || workspaceList[0]?.id || "";
        if (nextWorkspaceId && nextWorkspaceId !== selectedWorkspaceId) {
          setSelectedWorkspaceId(nextWorkspaceId);
        }
        const [workspace, projects, favorites, repositoryStatusResponse] = await Promise.all([
          nextWorkspaceId ? ncp003.getWorkspace(nextWorkspaceId) : Promise.resolve(null),
          nextWorkspaceId ? ncp003.listProjects(nextWorkspaceId) : Promise.resolve([]),
          nextWorkspaceId ? ncp003.listWorkspaceFavorites(nextWorkspaceId) : Promise.resolve([]),
          nextWorkspaceId ? ncp007.repositoryStatus(nextWorkspaceId) : Promise.resolve(null),
        ]);
        if (cancelled) return;
        setSelectedWorkspace(workspace || workspaceList.find((item) => item.id === nextWorkspaceId) || null);
        setWorkspaceProjects(projects);
        setWorkspaceFavorites(favorites);
        setRepositoryStatus(repositoryStatusResponse);
        setLoadState("ready");
      } catch (error) {
        if (cancelled) return;
        setLoadError(error);
        setLoadState(mapLoadState(error));
      }
    }
    void loadWorkspaceData();
    return () => {
      cancelled = true;
    };
  }, [seedData, selectedWorkspaceId, workspaceIdFallback, ncp003, ncp007]);

  useEffect(() => {
    if (!selectedWorkspaceId || seedData) return undefined;
    const storedRecent = loadStoredValue(session, selectedWorkspaceId, "recent", []);
    setRecentResources(Array.isArray(storedRecent) ? storedRecent : []);
    const storedEditors = loadStoredValue(session, selectedWorkspaceId, "openEditors", []);
    setOpenEditors(Array.isArray(storedEditors) ? storedEditors : []);
    const storedFilter = loadStoredValue(session, selectedWorkspaceId, "filter", "");
    setFilterText(typeof storedFilter === "string" ? storedFilter : "");
    const storedSelection = loadStoredValue(session, selectedWorkspaceId, "selectedResource", null);
    if (storedSelection && typeof storedSelection === "object") {
      setSelectedResource(storedSelection);
    }
    const storedExpanded = loadStoredValue(session, selectedWorkspaceId, "expanded", []);
    setExpandedPaths(new Set(Array.isArray(storedExpanded) ? storedExpanded : []));
    return undefined;
  }, [seedData, selectedWorkspaceId, session]);

  useEffect(() => {
    if (seedData) return undefined;
    if (!selectedWorkspaceId) return undefined;
    const current = openEditors.map((item) => ({ ...item }));
    storeValue(session, selectedWorkspaceId, "openEditors", current);
    return undefined;
  }, [openEditors, selectedWorkspaceId, seedData, session]);

  useEffect(() => {
    if (seedData) return undefined;
    if (!selectedWorkspaceId) return undefined;
    storeValue(session, selectedWorkspaceId, "recent", recentResources);
  }, [recentResources, selectedWorkspaceId, seedData, session]);

  useEffect(() => {
    if (seedData) return undefined;
    if (!selectedWorkspaceId) return undefined;
    storeValue(session, selectedWorkspaceId, "filter", filterText);
  }, [filterText, selectedWorkspaceId, seedData, session]);

  useEffect(() => {
    if (seedData) return undefined;
    if (!selectedWorkspaceId) return undefined;
    storeValue(session, selectedWorkspaceId, "selectedResource", selectedResource);
  }, [selectedResource, selectedWorkspaceId, seedData, session]);

  const debouncedSearch = useDebouncedValue(searchQuery, 250);
  const debouncedFilter = useDebouncedValue(filterText, 150);

  useEffect(() => {
    if (seedData) return undefined;
    if (!selectedWorkspaceId || !debouncedSearch.trim()) {
      setSearchResults([]);
      setSearchState("idle");
      return undefined;
    }
    let cancelled = false;
    const controller = new AbortController();
    abortRef.current = controller;
    setSearchState("loading");
    ncp007
      .repositorySearch(selectedWorkspaceId, debouncedSearch.trim(), ".", controller.signal)
      .then((payload) => {
        if (cancelled) return;
        setSearchResults(ensureArray(payload?.matches));
        setSearchState("ready");
      })
      .catch((error) => {
        if (cancelled) return;
        setSearchResults([]);
        setSearchState(error?.code === "repository_path_forbidden" ? "error" : "error");
      });
    return () => {
      cancelled = true;
      controller.abort();
    };
  }, [debouncedSearch, selectedWorkspaceId, seedData, ncp007]);

  const selectedWorkspaceState = selectedWorkspace || workspaces.find((item) => item.id === selectedWorkspaceId) || workspaces[0] || null;

  async function refreshWorkspace(workspaceId = selectedWorkspaceId) {
    if (!workspaceId) return;
    setLoadState("loading");
    try {
      const [workspace, projects, favorites, repositoryStatusResponse] = await Promise.all([
        ncp003.getWorkspace(workspaceId),
        ncp003.listProjects(workspaceId),
        ncp003.listWorkspaceFavorites(workspaceId),
        ncp007.repositoryStatus(workspaceId),
      ]);
      setSelectedWorkspace(workspace);
      setWorkspaceProjects(projects);
      setWorkspaceFavorites(favorites);
      setRepositoryStatus(repositoryStatusResponse);
      setLoadState("ready");
    } catch (error) {
      setLoadError(error);
      setLoadState(mapLoadState(error));
    }
  }

  async function loadRepositoryTree(workspaceId = selectedWorkspaceId) {
    if (!workspaceId) return;
    setLoadState("loading");
    try {
      const payload = await ncp007.repositoryTree(workspaceId, ".");
      setRepositoryEntries(ensureArray(payload?.tree));
      setRepositoryTreeLoaded(true);
      setLoadState("ready");
    } catch (error) {
      setLoadError(error);
      setLoadState(mapLoadState(error));
    }
  }

  async function refreshRepository() {
    await refreshWorkspace();
    if (repositoryTreeLoaded) {
      await loadRepositoryTree();
    }
  }

  async function toggleExpand(node, forceExpanded) {
    const next = new Set(expandedPaths);
    const expanded = typeof forceExpanded === "boolean" ? forceExpanded : !next.has(node.id);
    if (expanded) {
      next.add(node.id);
      if (node.type === "repository" && !repositoryTreeLoaded) {
        await loadRepositoryTree(selectedWorkspaceId);
      }
    } else {
      next.delete(node.id);
    }
    setExpandedPaths(next);
  }

  function rememberRecent(resource) {
    if (!resource) return;
    const next = [{ ...resource, lastViewedAt: new Date().toISOString() }, ...recentResources.filter((item) => item.id !== resource.id)].slice(0, 20);
    setRecentResources(next);
  }

  async function selectNode(node) {
    setSelectedResource(node);
    rememberRecent(node);
    if (node.type === "file") {
      await previewFile(node);
      if (!openEditors.some((item) => item.id === node.id)) {
        setOpenEditors((current) => [{ id: node.id, name: node.name, path: node.path, pinned: false, language: node.language, gitStatus: node.gitStatus, sizeBytes: node.sizeBytes, workspaceId: node.workspaceId }, ...current].slice(0, 12));
      }
    }
  }

  async function previewFile(node) {
    if (!selectedWorkspaceId || !node?.path) return;
    if (!isSupportedTextFile(node.path)) {
      setPreview({ state: "unsupported", language: languageFromPath(node.path), encoding: "utf-8", sizeLabel: "Unavailable" });
      return;
    }
    setPreview({ state: "loading", message: `Loading ${node.path}` });
    try {
      const payload = await ncp007.repositoryFile(selectedWorkspaceId, node.path);
      const content = String(payload?.content || "");
      if (/\x00/.test(content)) {
        setPreview({ state: "binary", language: languageFromPath(node.path), encoding: "binary", sizeLabel: typeof node.sizeBytes === "number" ? `${node.sizeBytes.toLocaleString()} bytes` : "Unavailable" });
        return;
      }
      const { lines, truncated, lineCount } = readPreviewLines(content, 260);
      setPreview({
        state: "ready",
        lines,
        truncated,
        lineCount,
        language: payload?.language || languageFromPath(node.path),
        encoding: "utf-8",
        sizeLabel: typeof node.sizeBytes === "number" ? `${node.sizeBytes.toLocaleString()} bytes` : `${content.length.toLocaleString()} chars`,
      });
    } catch (error) {
      if (error?.code === "repository_file_not_found") {
        setPreview({ state: "not_found", message: error.message, language: languageFromPath(node.path), encoding: "utf-8" });
        return;
      }
      if (error?.status === 403 || error?.code === "repository_path_forbidden") {
        setPreview({ state: "forbidden", message: error.message, language: languageFromPath(node.path), encoding: "utf-8" });
        return;
      }
      if (error?.code === "repository_file_not_found" || error?.code === "repository_file_binary") {
        setPreview({ state: "binary", message: error.message, language: languageFromPath(node.path), encoding: "binary" });
        return;
      }
      setPreview({ state: "error", message: error?.message || "Unable to load file preview.", language: languageFromPath(node.path), encoding: "utf-8" });
    }
  }

  async function openResource(node) {
    if (!node) return;
    setSelectedResource(node);
    rememberRecent(node);
    if (node.type === "file") {
      await previewFile(node);
    }
  }

  async function addFavorite(node) {
    if (!selectedWorkspaceId || !node) return;
    const route = `explorer://${selectedWorkspaceId}/${node.type}/${encodeURIComponent(node.path || node.id)}`;
    const favorite = await ncp003.addWorkspaceFavorite(selectedWorkspaceId, { label: node.name, route });
    setWorkspaceFavorites((current) => [favorite, ...current.filter((item) => item.id !== favorite.id)]);
  }

  async function removeFavorite(node) {
    if (!selectedWorkspaceId || !node) return;
    const favorite = ensureArray(workspaceFavorites).find((item) => item.route === `explorer://${selectedWorkspaceId}/${node.type}/${encodeURIComponent(node.path || node.id)}` || item.label === node.name);
    if (!favorite) return;
    await ncp003.removeWorkspaceFavorite(selectedWorkspaceId, favorite.id);
    setWorkspaceFavorites((current) => current.filter((item) => item.id !== favorite.id));
  }

  async function copyPath(node, repositoryRelative = false) {
    if (!node?.path || typeof navigator === "undefined" || !navigator.clipboard?.writeText) return;
    const text = repositoryRelative ? node.path : node.path;
    await navigator.clipboard.writeText(text);
  }

  function openGovernedWorkflow(node) {
    onFocusNav?.("Explorer");
    navigate?.("/novacodepro/development/workspaces");
    rememberRecent(node);
  }

  function collapseAll() {
    setExpandedPaths(new Set());
    setContextMenuNode(null);
    setContextMenuItems([]);
  }

  function handleContextMenu(node) {
    setContextMenuNode(node);
    const favoriteRoute = `explorer://${selectedWorkspaceId}/${node.type}/${encodeURIComponent(node.path || node.id)}`;
    const isFavourite = ensureArray(workspaceFavorites).some((item) => item.route === favoriteRoute || item.label === node.name);
    setContextMenuItems(
      explorerActionMenu(node, {
        isFavourite,
        canLoadRepository: Boolean(selectedWorkspaceId),
        onAddFavourite: addFavorite,
        onRemoveFavourite: removeFavorite,
        onOpenFile: previewFile,
        onOpenResource: openResource,
        onRefresh: async (item) => {
          if (item.type === "repository" && !repositoryTreeLoaded) {
            await loadRepositoryTree();
          } else {
            await refreshWorkspace();
          }
        },
        onCopyPath: (item) => copyPath(item, false),
        onCopyRepositoryPath: (item) => copyPath(item, true),
        onOpenDevelopmentStudio: openGovernedWorkflow,
        onClearRecent: () => {
          setRecentResources([]);
        },
      }),
    );
  }

  function clearSearch() {
    setSearchQuery("");
    setSearchResults([]);
    setSearchState("idle");
  }

  function clearRecent() {
    setRecentResources([]);
  }

  function closeEditor(editor) {
    setOpenEditors((current) => current.filter((item) => item.id !== editor.id));
  }

  function closeAllEditors() {
    setOpenEditors([]);
  }

  function pinEditor(editor) {
    setOpenEditors((current) => current.map((item) => (item.id === editor.id ? { ...item, pinned: !item.pinned } : item)));
  }

  function selectOpenEditor(editor) {
    const node = {
      id: editor.id,
      type: "file",
      name: editor.name,
      path: editor.path,
      workspaceId: selectedWorkspaceId,
      organizationId: session?.organization?.id || session?.tenant?.id || session?.tenant_id || "",
      language: editor.language || languageFromPath(editor.path),
      gitStatus: editor.gitStatus || "Preview",
      sizeBytes: editor.sizeBytes,
      metadata: { source: "open-editor" },
    };
    setSelectedResource(node);
    void previewFile(node);
  }

  function openSelectedResource(node) {
    setSelectedResource(node);
    if (node.type === "file") {
      void previewFile(node);
    }
  }

  function selectWorkspace(workspaceId) {
    setSelectedWorkspaceId(workspaceId);
    const workspace = workspaces.find((item) => item.id === workspaceId) || null;
    setSelectedWorkspace(workspace);
    setWorkspaceProjects([]);
    setWorkspaceFavorites([]);
    setRepositoryEntries([]);
    setRepositoryTreeLoaded(false);
    setPreview({ state: "idle" });
    setSelectedResource(null);
    setExpandedPaths(new Set());
    setLoadState("loading");
    void refreshWorkspace(workspaceId);
  }

  function submitSearch() {
    if (!searchQuery.trim()) return;
    if (!selectedWorkspaceId) return;
    setSearchState("loading");
    void ncp007
      .repositorySearch(selectedWorkspaceId, searchQuery.trim(), ".")
      .then((payload) => {
        setSearchResults(ensureArray(payload?.matches));
        setSearchState("ready");
      })
      .catch((error) => {
        setSearchResults([]);
        setSearchState(mapLoadState(error));
      });
  }

  const viewPreview = selectedResource?.type === "file" ? preview : { state: "idle" };

  const contextMenu = contextMenuNode
    ? contextMenuItems
    : explorerActionMenu(selectedResource || selectedWorkspaceState || { type: "workspace", name: "Workspace", path: "" }, {
        isFavourite: false,
        canLoadRepository: Boolean(selectedWorkspaceId),
        onAddFavourite: addFavorite,
        onRemoveFavourite: removeFavorite,
        onOpenFile: previewFile,
        onOpenResource: openResource,
        onRefresh: async () => refreshWorkspace(),
        onCopyPath: (item) => copyPath(item, false),
        onCopyRepositoryPath: (item) => copyPath(item, true),
        onOpenDevelopmentStudio: openGovernedWorkflow,
        onClearRecent: clearRecent,
      });

  return h(ExplorerView, {
    session,
    environment,
    activeRole,
    activeProject,
    workspaces,
    selectedWorkspaceId,
    selectedWorkspace: selectedWorkspaceState,
    workspaceProjects,
    workspaceFavorites,
    recentResources,
    openEditors,
    selectedResource,
    repositoryStatus,
    repositoryEntries,
    repositoryCategories,
    repositoryTreeLoaded,
    searchQuery,
    searchResults,
    searchState,
    preview: viewPreview,
    expandedPaths,
    loadState,
    loadError,
    filterText: debouncedFilter,
    onSelectWorkspace: selectWorkspace,
    onRefreshWorkspace: refreshWorkspace,
    onRefreshRepository: async () => {
      await refreshRepository();
      if (!repositoryTreeLoaded) {
        await loadRepositoryTree();
      }
    },
    onCollapseAll: collapseAll,
    onToggleExpand: toggleExpand,
    onSelectNode: openSelectedResource,
    onOpenFilePreview: previewFile,
    onOpenResource: openResource,
    onAddFavorite: addFavorite,
    onRemoveFavorite: removeFavorite,
    onCopyPath: copyPath,
    onCopyRepositoryPath: copyPath,
    onOpenDevelopmentStudio: openGovernedWorkflow,
    onClearRecent: clearRecent,
    onPinEditor: pinEditor,
    onCloseEditor: closeEditor,
    onCloseAllEditors: closeAllEditors,
    onSelectOpenEditor: selectOpenEditor,
    onFilterTextChange: setFilterText,
    onSearchQueryChange: setSearchQuery,
    onSearchSubmit: submitSearch,
    onClearSearch: clearSearch,
    onOpenContextMenu: handleContextMenu,
    onCloseContextMenu: () => {
      setContextMenuNode(null);
      setContextMenuItems([]);
    },
    contextMenuNode,
    contextMenuItems: contextMenu,
  });
}

export default StudioExplorer;
