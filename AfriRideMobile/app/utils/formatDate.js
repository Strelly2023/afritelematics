export function formatDate(value) {
  if (!value) return "Not recorded";
  return new Date(value).toLocaleString();
}
