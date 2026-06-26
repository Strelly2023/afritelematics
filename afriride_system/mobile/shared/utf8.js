export function toUtf8Bytes(input) {
  const text = String(input ?? "");

  if (typeof TextEncoder !== "undefined") {
    return new TextEncoder().encode(text);
  }

  if (typeof Buffer !== "undefined") {
    return Uint8Array.from(Buffer.from(text, "utf8"));
  }

  throw new Error("UTF-8 encoder unavailable in this environment");
}
