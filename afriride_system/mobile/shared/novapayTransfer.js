import React, { useEffect, useMemo, useState } from "react";
import { View } from "react-native";

import {
  ActionButton,
  Divider,
  ExpandableCard,
  Field,
  InfoRow,
  JsonCard,
  Pill,
  SectionCard,
  Timeline,
  formatCount,
  formatHash,
  formatMoney,
  humanizeStatus,
  normalizeText,
  statusTone,
} from "./novarideUi";
import {
  executeTransfer,
  getTransferFeatures,
  getTransferLimits,
  getTransferRails,
  quoteTransfer,
  verifyTransferReceipt,
} from "./novapayApiClient";

function safeArray(value) {
  return Array.isArray(value) ? value : [];
}

export function NovaPayTransferPanel({
  role,
  userId,
  title = "NovaPay Transfer",
  subtitle = "Protocol-driven payment flow with quotes, limits, payout methods, and receipts.",
  defaultRecipientName = "",
  defaultRecipientIdentifier = "",
  defaultRecipientCountry = "KE",
  defaultAmount = "100.00",
  defaultSourceCurrency = "AUD",
  defaultPayoutMethod = "bank_deposit",
  defaultUseCase = "transparent_pricing",
  mode = "send",
}) {
  const [recipientName, setRecipientName] = useState(defaultRecipientName);
  const [recipientIdentifier, setRecipientIdentifier] = useState(defaultRecipientIdentifier);
  const [recipientCountry, setRecipientCountry] = useState(defaultRecipientCountry);
  const [amount, setAmount] = useState(defaultAmount);
  const [sourceCurrency, setSourceCurrency] = useState(defaultSourceCurrency);
  const [payoutMethod, setPayoutMethod] = useState(defaultPayoutMethod);
  const [useCase, setUseCase] = useState(defaultUseCase);
  const [memo, setMemo] = useState("");
  const [quote, setQuote] = useState(null);
  const [receipt, setReceipt] = useState(null);
  const [verification, setVerification] = useState(null);
  const [features, setFeatures] = useState(null);
  const [limits, setLimits] = useState(null);
  const [rails, setRails] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const [featurePayload, limitPayload, railPayload] = await Promise.all([
          getTransferFeatures(),
          getTransferLimits(),
          getTransferRails(),
        ]);
        if (!cancelled) {
          setFeatures(featurePayload);
          setLimits(limitPayload);
          setRails(railPayload);
        }
      } catch (cause) {
        if (!cancelled) {
          setError(cause instanceof Error ? cause.message : "transfer_features_unavailable");
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const useCaseLabel = useMemo(() => {
    const selected = safeArray(features?.use_cases).find((entry) => entry.key === useCase);
    return normalizeText(selected?.label, "Transfer");
  }, [features?.use_cases, useCase]);

  const payoutLabel = useMemo(() => {
    const available = safeArray(features?.payout_methods);
    return available.includes(payoutMethod) ? payoutMethod : defaultPayoutMethod;
  }, [defaultPayoutMethod, features?.payout_methods, payoutMethod]);

  const routeLabel = useMemo(() => {
    if (quote?.route_class) {
      return humanizeStatus(quote.route_class, quote.route_class);
    }
    return "not quoted";
  }, [quote]);

  const topMetrics = useMemo(
    () => [
      {
        label: "Quote",
        value: quote ? formatHash(quote.quote_hash, "Pending") : "Pending",
        detail: quote ? quote.corridor : "Request a quote",
        tone: quote ? "success" : "accent",
      },
      {
        label: "Fee",
        value: quote ? formatMoney(quote.fee_amount) : "—",
        detail: quote ? "Transparent fee" : "Estimate before send",
        tone: quote ? "amber" : "neutral",
      },
      {
        label: "Destination",
        value: quote ? formatMoney(quote.destination_amount) : formatMoney(amount),
        detail: quote ? quote.destination_currency : sourceCurrency,
        tone: "success",
      },
      {
        label: "Limit",
        value: quote ? formatMoney(quote.transfer_limit) : "—",
        detail: quote ? payoutLabel : "Method selected",
        tone: "accent",
      },
    ],
    [amount, payoutLabel, quote, sourceCurrency],
  );

  const timeline = useMemo(
    () => [
      {
        label: "Recipient",
        detail: normalizeText(recipientName || recipientIdentifier || "Recipient"),
        done: Boolean(recipientIdentifier),
      },
      {
        label: "Quote",
        detail: quote ? quote.route_hint : "Request pricing",
        done: Boolean(quote),
      },
      {
        label: "Send",
        detail: receipt ? receipt.status : "Awaiting execution",
        done: Boolean(receipt),
      },
      {
        label: "Verify",
        detail: verification?.reason || "Receiver proof pending",
        done: Boolean(verification?.valid),
      },
    ],
    [quote, receipt, recipientIdentifier, recipientName, verification],
  );

  async function handleQuote() {
    setError("");
    setLoading(true);
    try {
      const payload = await quoteTransfer({
        role,
        userId,
        recipientName,
        recipientIdentifier,
        recipientCountry,
        amount,
        sourceCurrency,
        payoutMethod,
        useCase,
        memo,
      });
      setQuote(payload.quote || payload);
      setReceipt(null);
      setVerification(null);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "quote_failed");
    } finally {
      setLoading(false);
    }
  }

  async function handleExecute() {
    setError("");
    setLoading(true);
    try {
      const payload = await executeTransfer({
        role,
        userId,
        quote: quote || {
          recipient_name: recipientName,
          recipient_identifier: recipientIdentifier,
          recipient_country: recipientCountry,
          amount,
          source_currency: sourceCurrency,
          payout_method: payoutMethod,
          use_case: useCase,
        },
      });
      setReceipt(payload.receipt || payload);
      setVerification(null);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "transfer_failed");
    } finally {
      setLoading(false);
    }
  }

  async function handleVerify() {
    if (!receipt) {
      setError("quote_or_receipt_required");
      return;
    }
    setError("");
    setLoading(true);
    try {
      const payload = await verifyTransferReceipt({
        role,
        userId,
        receipt,
      });
      setVerification(payload);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "verification_failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <SectionCard
      title={title}
      eyebrow="NovaPay"
      action={<Pill label={quote ? "Quoted" : "Ready"} tone={quote ? "success" : "accent"} />}
    >
      <InfoRow label="Mode" value={mode === "send" ? "Sender wallet" : mode === "verify" ? "Receiver verification" : "Operator control"} />
      <InfoRow label="Use case" value={useCaseLabel} />
      <InfoRow label="Payout" value={payoutLabel} />
      <InfoRow label="Route" value={routeLabel} />
      <Divider />

      <Field label="Recipient name" value={recipientName} onChangeText={setRecipientName} placeholder="Family name" />
      <Field
        label="Recipient identifier"
        value={recipientIdentifier}
        onChangeText={setRecipientIdentifier}
        placeholder="Phone / wallet / bank ref"
      />
      <Field label="Recipient country" value={recipientCountry} onChangeText={setRecipientCountry} placeholder="KE" />
      <Field label="Amount" value={amount} onChangeText={setAmount} placeholder="100.00" />
      <Field label="Source currency" value={sourceCurrency} onChangeText={setSourceCurrency} placeholder="AUD" />
      <Field
        label="Payout method"
        value={payoutMethod}
        onChangeText={setPayoutMethod}
        placeholder="bank_deposit"
      />
      <Field label="Use case" value={useCase} onChangeText={setUseCase} placeholder="transparent_pricing" />
      <Field label="Memo" value={memo} onChangeText={setMemo} placeholder="Invoice / purpose" />

      <View style={{ flexDirection: "row", gap: 10, marginTop: 10 }}>
        <ActionButton title="Get quote" onPress={handleQuote} disabled={loading} flex />
        <ActionButton title="Send transfer" tone="secondary" onPress={handleExecute} disabled={loading} flex />
      </View>
      <View style={{ flexDirection: "row", gap: 10, marginTop: 10 }}>
        <ActionButton title="Verify receipt" tone="secondary" onPress={handleVerify} disabled={loading || !receipt} flex />
        <ActionButton
          title="Reset"
          tone="secondary"
          onPress={() => {
            setQuote(null);
            setReceipt(null);
            setVerification(null);
            setError("");
          }}
          disabled={loading}
          flex
        />
      </View>

      <Divider />
      <Timeline items={timeline} />

      <Divider />
      <SectionCard title="Pricing snapshot" eyebrow="Fees and rate" action={<Pill label={quote ? "Live quote" : "Estimate"} tone={quote ? "success" : "neutral"} />}>
        <InfoRow label="Amount" value={formatMoney(quote?.source_amount || amount)} />
        <InfoRow label="Fee" value={formatMoney(quote?.fee_amount)} />
        <InfoRow label="Total debit" value={formatMoney(quote?.total_debit)} />
        <InfoRow label="Mid-market rate" value={normalizeText(quote?.mid_market_rate, "—")} />
        <InfoRow label="Destination amount" value={formatMoney(quote?.destination_amount)} />
        <InfoRow label="Limit" value={formatMoney(quote?.transfer_limit)} />
        <InfoRow label="ETA" value={normalizeText(quote?.eta, "—")} />
      </SectionCard>

      <SectionCard title="Feature coverage" eyebrow="Product">
        <InfoRow label="Global coverage" value={features?.global_coverage ? "Yes" : "No"} />
        <InfoRow label="Cash pickups" value={features?.cash_pickups ? "Yes" : "No"} />
        <InfoRow label="Bank deposit" value={features?.bank_deposit ? "Yes" : "No"} />
        <InfoRow label="Fast international" value={features?.fast_low_cost_international ? "Yes" : "No"} />
        <InfoRow label="Domestic transfers" value={features?.domestic_transfers ? "Yes" : "No"} />
        <InfoRow label="Best money transfer app" value={features?.best_money_transfer_app || "NovaPay"} tone="success" />
      </SectionCard>

      <SectionCard title="Supported rails" eyebrow="Backend">
        <JsonCard value={rails} empty="Rails not loaded yet." />
      </SectionCard>

      <SectionCard title="Receipt" eyebrow="Transfer proof">
        <JsonCard value={quote} empty="Quote not loaded yet." />
        <JsonCard value={receipt} empty="Receipt not generated yet." />
        <JsonCard value={verification} empty="Verification not run yet." />
      </SectionCard>

      <ExpandableCard
        title="Transfer notes"
        eyebrow="Use cases"
        summary="Transparent pricing, fast low-cost international, travelers, large transfers, and domestic transfers."
        defaultOpen={false}
      >
        <InfoRow label="Transparent pricing" value="Mid-market exchange rate display and explicit fee breakdown." />
        <InfoRow label="Fast international" value="Best-effort low-cost route with payout method selection." />
        <InfoRow label="Frequent traveler" value="Multi-currency budgeting and rail visibility." />
        <InfoRow label="Large transfers" value="Higher review threshold with operator control." />
        <InfoRow label="Domestic" value="PayID or local rail selection." />
      </ExpandableCard>

      {error ? <InfoRow label="Error" value={error} tone="danger" /> : null}
    </SectionCard>
  );
}
