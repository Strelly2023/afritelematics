export function formatMoney(value, currency = "AUD") {
  const amount = Number.isFinite(Number(value)) ? Number(value) : 0;
  return new Intl.NumberFormat("en-AU", {
    style: "currency",
    currency,
  }).format(amount);
}
