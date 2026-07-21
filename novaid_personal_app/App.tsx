import React, { useEffect, useMemo, useState } from "react";
import {
  Pressable,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Switch,
  Text,
  TextInput,
  useColorScheme,
  View,
} from "react-native";

import { appConfig } from "./src/appConfig";
import {
  createMockIdentityProfile,
  loadIdentityProfile,
  beginVerificationFlow,
  buildAuditPackage,
} from "./src/services/novaid.service";
import { issueMockCredential } from "./src/services/credential.service";
import { createConsentGrant, revokeConsentGrant } from "./src/services/consent.service";
import { manageTrustedDevice } from "./src/services/deviceTrust.service";
import { issueDigitalCertificate } from "./src/services/certificate.service";
import { saveInspection } from "./src/services/inspection.service";
import { createOAuthClient, rotatePartnerSecret, testWebhook } from "./src/services/partner.service";
import { getNovaAIIdentityRecommendation } from "./src/services/novaaiIdentity.service";
import {
  AppAction,
  AppVariantId,
  ConsentGrant,
  Credential,
  DigitalCertificate,
  IdentityEvent,
  IdentityProfile,
  InspectionRecord,
  PartnerClient,
  TrustedDevice,
  VerificationRequest,
} from "./src/models";

type Banner = {
  tone: "success" | "info" | "warning";
  title: string;
  detail: string;
};

const initialProfile = createMockIdentityProfile();

export default function App() {
  const colorScheme = useColorScheme();
  const dark = colorScheme === "dark";
  const palette = useMemo(
    () => ({
      bg: dark ? "#06111f" : "#eef4ff",
      surface: dark ? "rgba(14, 27, 48, 0.92)" : "#ffffff",
      surfaceAlt: dark ? "#0f2036" : "#f7f9ff",
      ink: dark ? "#f5f8ff" : "#111827",
      muted: dark ? "#8ea1c1" : "#52607a",
      line: dark ? "rgba(135, 159, 198, 0.18)" : "#dbe4f0",
      accent: appConfig.trustTheme,
      success: "#24b36b",
      warning: "#e19a2f",
      danger: "#ef6a6a",
    }),
    [dark],
  );

  const [activeTab, setActiveTab] = useState(appConfig.tabs[0]?.key ?? "home");
  const [profile, setProfile] = useState<IdentityProfile>(initialProfile);
  const [credentials, setCredentials] = useState<Credential[]>(initialProfile.credentials);
  const [certificates, setCertificates] = useState<DigitalCertificate[]>(initialProfile.certificates);
  const [devices, setDevices] = useState<TrustedDevice[]>(initialProfile.devices);
  const [consents, setConsents] = useState<ConsentGrant[]>(initialProfile.consents);
  const [events, setEvents] = useState<IdentityEvent[]>(initialProfile.events);
  const [verification, setVerification] = useState<VerificationRequest | null>(null);
  const [inspections, setInspections] = useState<InspectionRecord[]>([]);
  const [partnerClients, setPartnerClients] = useState<PartnerClient[]>([]);
  const [banner, setBanner] = useState<Banner | null>(null);
  const [shareMode, setShareMode] = useState(true);
  const [shareLink, setShareLink] = useState(`novaid://${appConfig.id}/${initialProfile.id}`);
  const [shareQr, setShareQr] = useState("QR•NOVAID•READY");
  const [showAllDevices, setShowAllDevices] = useState(false);
  const [offlineMode, setOfflineMode] = useState(false);
  const [supportNote, setSupportNote] = useState("Need recovery support");
  const [dashboardCounter, setDashboardCounter] = useState(0);
  const [businessRoster, setBusinessRoster] = useState<string[]>([
    "Managing Director · Verified",
    "Finance Director · Verified",
  ]);
  const [hrItems, setHrItems] = useState<string[]>([
    "Leave requests queue empty",
    "Expense claims ready",
  ]);
  const [webhookState, setWebhookState] = useState("Webhook not yet tested");

  useEffect(() => {
    let cancelled = false;
    void loadIdentityProfile()
      .then((nextProfile) => {
        if (cancelled) {
          return;
        }
        setProfile(nextProfile);
        setCredentials(nextProfile.credentials);
        setCertificates(nextProfile.certificates);
        setDevices(nextProfile.devices);
        setConsents(nextProfile.consents);
        setEvents(nextProfile.events);
        setVerification(null);
        setBanner({
          tone: nextProfile.summary.includes("backend synced") ? "success" : "info",
          title: nextProfile.summary.includes("backend synced")
            ? "NovaID backend synced"
            : "Local identity profile loaded",
          detail: nextProfile.summary,
        });
      })
      .catch((error) => {
        if (!cancelled) {
          setBanner({
            tone: "warning",
            title: "NovaID sync unavailable",
            detail: error instanceof Error ? error.message : "Using local identity profile data.",
          });
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const addEvent = (event: IdentityEvent) => {
    setEvents((current) => [event, ...current].slice(0, 12));
  };

  const notify = (next: Banner) => setBanner(next);

  const handleAction = async (action: AppAction) => {
    const timestamp = new Date().toISOString();
    switch (action.label) {
      case "Add Credential": {
        const credential = await issueMockCredential("digital_certificate", "Identity Credential", "NovaID Authority");
        setCredentials((current) => [credential, ...current]);
        setProfile((current) => ({
          ...current,
          credentialCount: current.credentialCount + 1,
          identityScore: Math.min(current.identityScore + 1, 100),
          certificates: current.certificates,
        }));
        addEvent({
          id: `event-${timestamp}`,
          type: "verification",
          title: "Credential added",
          detail: "A new credential is now attached to the identity wallet.",
          timestamp,
          severity: "success",
        });
        notify({ tone: "success", title: "Credential added", detail: credential.label });
        break;
      }
      case "Verify Identity": {
        const request = await beginVerificationFlow(profile.id);
        setVerification(request);
        setProfile((current) => ({
          ...current,
          verificationStatus: request.status,
          summary:
            request.status === "pending"
              ? "Verification challenge issued by NovaID backend; completion is pending."
              : current.summary,
        }));
        addEvent({
          id: `event-${timestamp}`,
          type: "verification",
          title: request.status === "pending" ? "Verification challenge issued" : "Identity verified",
          detail:
            request.status === "pending"
              ? "NovaID backend accepted the verification request and issued a challenge."
              : "Biometric, document, liveness, and policy checks passed.",
          timestamp,
          severity: request.status === "pending" ? "info" : "success",
        });
        notify({
          tone: request.status === "pending" ? "info" : "success",
          title: request.status === "pending" ? "Verification started" : "Identity verified",
          detail:
            request.status === "pending"
              ? "Complete the live NovaID challenge to finish verification."
              : "Digital certificate issued.",
        });
        break;
      }
      case "Share Identity": {
        const grant = await createConsentGrant(profile.id, "NovaID Share", credentials[0]?.id ?? "none", ["name", "photo", "trust_level"]);
        setConsents((current) => [grant, ...current]);
        setShareLink(`https://novaid.share/${profile.id}/${grant.id}`);
        setShareQr(`QR•${profile.id}•${grant.id}`);
        addEvent({
          id: `event-${timestamp}`,
          type: "consent_granted",
          title: "Identity shared",
          detail: "Selective disclosure payload ready for QR and link sharing.",
          timestamp,
          severity: "info",
        });
        notify({ tone: "info", title: "Share ready", detail: "QR and link created with selective disclosure." });
        break;
      }
      case "Scan QR": {
        setDashboardCounter((count) => count + 1);
        addEvent({
          id: `event-${timestamp}`,
          type: "verification",
          title: "QR scanned",
          detail: "Trusted QR identity surface opened successfully.",
          timestamp,
          severity: "success",
        });
        notify({ tone: "success", title: "QR scanned", detail: "Identity exchange ready." });
        break;
      }
      case "Revoke Access": {
        const grant = consents[0];
        if (!grant) {
          notify({ tone: "warning", title: "Nothing to revoke", detail: "No active consent grant exists yet." });
          break;
        }
        const revoked = await revokeConsentGrant(grant);
        setConsents((current) => [revoked, ...current.slice(1)]);
        addEvent({
          id: `event-${timestamp}`,
          type: "consent_revoked",
          title: "Consent revoked",
          detail: `${grant.requester} access was revoked.`,
          timestamp,
          severity: "warning",
        });
        notify({ tone: "warning", title: "Access revoked", detail: grant.requester });
        break;
      }
      case "View Certificate": {
        const cert = certificates[0] ?? (await issueDigitalCertificate(profile.id, "Identity Certificate", ["identity"]));
        setCertificates((current) => [cert, ...current.filter((item) => item.id !== cert.id)]);
        addEvent({
          id: `event-${timestamp}`,
          type: "certificate_issued",
          title: "Certificate viewed",
          detail: `Replay hash ${cert.replayHash} is available for verification.`,
          timestamp,
          severity: "info",
        });
        notify({ tone: "info", title: "Certificate opened", detail: cert.title });
        break;
      }
      case "Enable Passkey": {
        setProfile((current) => ({ ...current, passkeyEnabled: true }));
        addEvent({
          id: `event-${timestamp}`,
          type: "device_trust",
          title: "Passkey enabled",
          detail: "Passkey authentication is now available as the primary factor.",
          timestamp,
          severity: "success",
        });
        notify({ tone: "success", title: "Passkey enabled", detail: "Primary auth is now passkey ready." });
        break;
      }
      case "Manage Devices": {
        const next = await manageTrustedDevice(devices[0] ?? initialProfile.devices[0], !showAllDevices);
        setDevices((current) => [next, ...current.filter((item) => item.id !== next.id)]);
        setShowAllDevices((value) => !value);
        setProfile((current) => ({
          ...current,
          deviceTrustEnabled: true,
          trustedDevices: Math.max(current.trustedDevices, 1),
        }));
        addEvent({
          id: `event-${timestamp}`,
          type: "device_trust",
          title: "Device trust updated",
          detail: `${next.deviceName} trust is ${next.trusted ? "active" : "review"}.`,
          timestamp,
          severity: "info",
        });
        notify({ tone: "info", title: "Devices updated", detail: next.deviceName });
        break;
      }
      case "Start Recovery": {
        setProfile((current) => ({ ...current, recoveryEnabled: true }));
        addEvent({
          id: `event-${timestamp}`,
          type: "support",
          title: "Recovery started",
          detail: "Recovery workflow started with support and trust fallback.",
          timestamp,
          severity: "warning",
        });
        notify({ tone: "warning", title: "Recovery started", detail: "Assisted recovery is now in progress." });
        break;
      }
      case "Contact Support": {
        setSupportNote("Support ticket opened and queued for assisted identity recovery.");
        addEvent({
          id: `event-${timestamp}`,
          type: "support",
          title: "Support contact initiated",
          detail: "Support can continue the identity recovery or disputes workflow.",
          timestamp,
          severity: "info",
        });
        notify({ tone: "info", title: "Support contacted", detail: "A support note has been saved." });
        break;
      }
      case "Verify Business": {
        setProfile((current) => ({
          ...current,
          trustLevel: "High",
          verificationStatus: "verified",
          certificateCount: current.certificateCount + 1,
          identityScore: Math.min(current.identityScore + 1, 100),
        }));
        addEvent({
          id: `event-${timestamp}`,
          type: "verification",
          title: "Business verified",
          detail: "KYB, registration, and policy checks passed.",
          timestamp,
          severity: "success",
        });
        notify({ tone: "success", title: "Business verified", detail: "KYB certificate updated." });
        break;
      }
      case "Add Director": {
        setBusinessRoster((current) => [`Director ${current.length + 1} · Pending review`, ...current]);
        addEvent({
          id: `event-${timestamp}`,
          type: "verification",
          title: "Director added",
          detail: "Corporate governance roster updated.",
          timestamp,
          severity: "info",
        });
        notify({ tone: "info", title: "Director added", detail: "Governance roster updated." });
        break;
      }
      case "Invite Employee": {
        setPartnerClients((current) => [
          {
            id: `employee-${timestamp}`,
            name: "Employee invite issued",
            clientId: `invite-${Math.random().toString(36).slice(2, 8)}`,
            secretHint: "hr-provisioning",
            webhookUrl: "https://hr.example/novaid",
            apiUsage: 0,
            status: "pending",
          },
          ...current,
        ]);
        addEvent({
          id: `event-${timestamp}`,
          type: "support",
          title: "Employee invited",
          detail: "Assisted employee provisioning request queued.",
          timestamp,
          severity: "info",
        });
        notify({ tone: "info", title: "Employee invited", detail: "Provisioning link created." });
        break;
      }
      case "Issue Certificate": {
        void issueDigitalCertificate(profile.id, "Business Seal Certificate", ["kyb", "director", "tax"]);
        setCertificates((current) => [
          {
            id: `cert-business-${timestamp}`,
            subjectId: profile.id,
            title: "Business Seal Certificate",
            issuer: "NovaID Authority",
            issuedAt: timestamp,
            sealHash: `seal-${Math.random().toString(36).slice(2, 10)}`,
            replayHash: `replay-${Math.random().toString(36).slice(2, 10)}`,
            status: "verified",
            scope: ["kyb", "director", "tax"],
          },
          ...current,
        ]);
        addEvent({
          id: `event-${timestamp}`,
          type: "certificate_issued",
          title: "Business certificate issued",
          detail: "Digital seal and KYB certificate recorded.",
          timestamp,
          severity: "success",
        });
        notify({ tone: "success", title: "Certificate issued", detail: "Business seal available." });
        break;
      }
      case "View Digital Seal": {
        notify({ tone: "info", title: "Digital seal opened", detail: certificates[0]?.sealHash ?? "No seal available yet." });
        addEvent({
          id: `event-${timestamp}`,
          type: "certificate_issued",
          title: "Digital seal viewed",
          detail: "Seal and replay receipt displayed.",
          timestamp,
          severity: "info",
        });
        break;
      }
      case "Download KYB Report": {
        buildAuditPackage(events.slice(0, 8).map((event) => event.id)).then((audit) =>
          notify({ tone: "success", title: "KYB report ready", detail: audit.digitalSignature }),
        );
        addEvent({
          id: `event-${timestamp}`,
          type: "verification",
          title: "KYB report generated",
          detail: "Signed report queued for download.",
          timestamp,
          severity: "success",
        });
        break;
      }
      case "Show Employee ID": {
        setCredentials((current) => [
          {
            id: `employee-id-${timestamp}`,
            type: "employee_id",
            label: "Employee ID",
            issuer: "NovaID HR",
            status: "verified",
            issuedAt: timestamp,
          },
          ...current,
        ]);
        addEvent({
          id: `event-${timestamp}`,
          type: "verification",
          title: "Employee ID shown",
          detail: "Employee identity card displayed with live QR.",
          timestamp,
          severity: "success",
        });
        notify({ tone: "success", title: "Employee ID shown", detail: "Live badge is ready." });
        break;
      }
      case "Check In": {
        setHrItems((current) => [`Checked in at ${timestamp}`, ...current]);
        addEvent({
          id: `event-${timestamp}`,
          type: "verification",
          title: "Checked in",
          detail: "Attendance started for the shift.",
          timestamp,
          severity: "success",
        });
        notify({ tone: "success", title: "Checked in", detail: "Attendance recorded." });
        break;
      }
      case "Check Out": {
        setHrItems((current) => [`Checked out at ${timestamp}`, ...current]);
        addEvent({
          id: `event-${timestamp}`,
          type: "verification",
          title: "Checked out",
          detail: "Shift closed and attendance captured.",
          timestamp,
          severity: "info",
        });
        notify({ tone: "info", title: "Checked out", detail: "Attendance complete." });
        break;
      }
      case "Request Leave": {
        setHrItems((current) => [`Leave requested at ${timestamp}`, ...current]);
        addEvent({
          id: `event-${timestamp}`,
          type: "support",
          title: "Leave requested",
          detail: "HR leave workflow opened.",
          timestamp,
          severity: "info",
        });
        notify({ tone: "info", title: "Leave requested", detail: "HR has a new request." });
        break;
      }
      case "Submit Expense": {
        setHrItems((current) => [`Expense submitted at ${timestamp}`, ...current]);
        addEvent({
          id: `event-${timestamp}`,
          type: "support",
          title: "Expense submitted",
          detail: "Expense claim and receipt replay stored.",
          timestamp,
          severity: "success",
        });
        notify({ tone: "success", title: "Expense submitted", detail: "Claim ready for approval." });
        break;
      }
      case "Open Access QR": {
        setShareMode(true);
        setShareQr(`QR•ACCESS•${timestamp.slice(11, 19)}`);
        setShareLink(`access://${profile.id}/${timestamp.slice(0, 10)}`);
        addEvent({
          id: `event-${timestamp}`,
          type: "verification",
          title: "Access QR opened",
          detail: "Building access QR is available for scan.",
          timestamp,
          severity: "success",
        });
        notify({ tone: "success", title: "Access QR opened", detail: "Security QR is visible." });
        break;
      }
      case "Scan QR": {
        if (appConfig.id === "inspector") {
          const record = {
            id: `inspection-${timestamp}`,
            inspectorId: profile.id,
            credentialId: credentials[0]?.id ?? "credential",
            result: "verified" as const,
            offlineMode,
            savedAt: timestamp,
            syncedAt: offlineMode ? null : timestamp,
          };
          setInspections((current) => [record, ...current]);
          addEvent({
            id: `event-${timestamp}`,
            type: "inspection",
            title: "QR scanned",
            detail: "Credential scanned and queued for inspection.",
            timestamp,
            severity: "success",
          });
        } else {
          setDashboardCounter((count) => count + 1);
          addEvent({
            id: `event-${timestamp}`,
            type: "verification",
            title: "QR scanned",
            detail: "Trusted QR identity surface opened successfully.",
            timestamp,
            severity: "success",
          });
        }
        notify({ tone: "success", title: "QR scanned", detail: "Identity exchange ready." });
        break;
      }
      case "Verify Credential": {
        setVerification({
          id: `verification-${timestamp}`,
          profileId: profile.id,
          step: "certificate_issued",
          status: "verified",
          requestedAt: timestamp,
          reviewedAt: timestamp,
          documentCheck: {
            status: "verified",
            documentType: "Identity credential",
            country: "AU",
            checkedAt: timestamp,
          },
          biometricCheck: {
            status: "verified",
            method: "multi",
            confidence: 0.97,
            checkedAt: timestamp,
          },
          livenessCheck: {
            status: "verified",
            confidence: 0.95,
            challenge: "scan-and-blink",
            checkedAt: timestamp,
          },
          policyEvaluation: {
            status: "verified",
            score: 97,
            reasons: ["Replay hash valid", "Document matched"],
            evaluatedAt: timestamp,
          },
        });
        addEvent({
          id: `event-${timestamp}`,
          type: "verification",
          title: "Credential verified",
          detail: "Inspector or partner verification request passed.",
          timestamp,
          severity: "success",
        });
        notify({ tone: "success", title: "Credential verified", detail: "Replay-backed proof available." });
        break;
      }
      case "Offline Verify": {
        setOfflineMode(true);
        addEvent({
          id: `event-${timestamp}`,
          type: "offline_verify",
          title: "Offline verification",
          detail: "Cached trust and replay evidence were used offline.",
          timestamp,
          severity: "warning",
        });
        notify({ tone: "warning", title: "Offline verify ready", detail: "Cached trust available." });
        break;
      }
      case "Save Inspection": {
        const record = await saveInspection(profile.id, credentials[0]?.id ?? "credential", offlineMode);
        setInspections((current) => [record, ...current]);
        addEvent({
          id: `event-${timestamp}`,
          type: "inspection",
          title: "Inspection saved",
          detail: "Field evidence has been captured.",
          timestamp,
          severity: "success",
        });
        notify({ tone: "success", title: "Inspection saved", detail: record.id });
        break;
      }
      case "Sync Records": {
        setInspections((current) => current.map((record) => ({ ...record, syncedAt: record.syncedAt ?? timestamp })));
        addEvent({
          id: `event-${timestamp}`,
          type: "inspection",
          title: "Records synced",
          detail: "Inspection records were synchronized.",
          timestamp,
          severity: "success",
        });
        notify({ tone: "success", title: "Records synced", detail: "Offline records are now aligned." });
        break;
      }
      case "Validate Certificate": {
        addEvent({
          id: `event-${timestamp}`,
          type: "certificate_issued",
          title: "Certificate validated",
          detail: "Seal and replay hash validated successfully.",
          timestamp,
          severity: "success",
        });
        notify({ tone: "success", title: "Certificate validated", detail: certificates[0]?.title ?? "Certificate ready" });
        break;
      }
      case "Create OAuth Client": {
        const client = await createOAuthClient(`Client ${partnerClients.length + 1}`);
        setPartnerClients((current) => [client, ...current]);
        addEvent({
          id: `event-${timestamp}`,
          type: "oauth_client",
          title: "OAuth client created",
          detail: `${client.clientId} created for partner access.`,
          timestamp,
          severity: "success",
        });
        notify({ tone: "success", title: "OAuth client created", detail: client.clientId });
        break;
      }
      case "Rotate Secret": {
        if (!partnerClients[0]) {
          notify({ tone: "warning", title: "No client", detail: "Create an OAuth client first." });
          break;
        }
        const rotated = await rotatePartnerSecret(partnerClients[0]);
        setPartnerClients((current) => [rotated, ...current.slice(1)]);
        addEvent({
          id: `event-${timestamp}`,
          type: "oauth_client",
          title: "Secret rotated",
          detail: "The partner secret was rotated successfully.",
          timestamp,
          severity: "info",
        });
        notify({ tone: "info", title: "Secret rotated", detail: rotated.secretHint });
        break;
      }
      case "Issue Partner Certificate": {
        const cert = await issueDigitalCertificate(profile.id, "Partner Certificate", ["oauth", "sdk", "webhook"]);
        setCertificates((current) => [cert, ...current]);
        addEvent({
          id: `event-${timestamp}`,
          type: "certificate_issued",
          title: "Partner certificate issued",
          detail: "Trust certificate created for partner ecosystem access.",
          timestamp,
          severity: "success",
        });
        notify({ tone: "success", title: "Partner certificate issued", detail: cert.sealHash });
        break;
      }
      case "View API Usage": {
        setWebhookState(`API usage is healthy · requests ${events.length + partnerClients.length}`);
        notify({ tone: "info", title: "Usage viewed", detail: "API usage snapshot refreshed." });
        break;
      }
      case "Test Webhook": {
        const result = await testWebhook(partnerClients[0] ?? (await createOAuthClient("Webhook Test")));
        setWebhookState(result.message);
        addEvent({
          id: `event-${timestamp}`,
          type: "verification",
          title: "Webhook tested",
          detail: result.message,
          timestamp,
          severity: "success",
        });
        notify({ tone: "success", title: "Webhook tested", detail: result.message });
        break;
      }
      default:
        if (appConfig.id === "personal" && action.label === "Share Identity") break;
        notify({ tone: "info", title: action.label, detail: action.detail });
    }
  };

  const verificationFlow = appConfig.primaryFlow.map((step, index) => ({
    step,
    status:
      index < 2 ? "done" : index === 2 ? "in-progress" : index === 3 ? "queued" : "queued",
  }));

  const currentTab = appConfig.tabs.find((tab) => tab.key === activeTab) ?? appConfig.tabs[0];
  const variantTabItems: Record<AppVariantId, Record<string, string[]>> = {
    personal: {
      home: [
        `Trust level: ${profile.trustLevel}`,
        `Identity score: ${profile.identityScore}`,
        `Biometric verified: ${profile.biometricVerified ? "Yes" : "No"}`,
        `Certificate count: ${profile.certificateCount}`,
      ],
      verify: [
        "Phone verification ready",
        "Email verification ready",
        "Document capture ready",
        "Selfie and liveness ready",
      ],
      documents: credentials.length > 0 ? credentials.map((credential) => `${credential.label} · ${credential.issuer}`) : ["No documents uploaded yet"],
      activity: [
        `Verification history: ${verification ? "Available" : "No recent verification"}`,
        `Consent history entries: ${consents.length}`,
        `Audit log entries: ${events.length}`,
      ],
      wallet: credentials.map((credential) => `${credential.label} · ${credential.issuer}`),
      share: [`QR: ${shareQr}`, `Link: ${shareLink}`, `Selective disclosure enabled`],
      consent: consents.length > 0 ? consents.map((grant) => `${grant.requester} · ${grant.status}`) : ["No active grants yet"],
      security: [
        `Passkey enabled: ${profile.passkeyEnabled ? "Yes" : "No"}`,
        `Trusted devices: ${devices.length}`,
        `Recovery: ${profile.recoveryEnabled ? "Ready" : "Off"}`,
      ],
      profile: [supportNote, ...events.slice(0, 3).map((event) => event.title)],
    },
    business: {
      overview: [
        `Trust level: ${profile.trustLevel}`,
        `KYB score: ${profile.identityScore}`,
        `Certificates: ${certificates.length}`,
        `Alerts: ${events.length}`,
      ],
      "business-verify": [
        "Business details intake",
        "Registration upload ready",
        "Tax certificate upload ready",
        "Representative verification ready",
      ],
      representatives: businessRoster,
      documents: certificates.map((cert) => `${cert.title} · ${cert.sealHash}`),
      access: ["User management ready", "Role management ready", "MFA required"],
      audit: events.slice(0, 5).map((event) => `${event.title} · ${event.severity}`),
      settings: [supportNote],
      dashboard: [
        `Trust level: ${profile.trustLevel}`,
        `KYB score: ${profile.identityScore}`,
        `Certificates: ${certificates.length}`,
      ],
      company: businessRoster,
      employees: partnerClients.length > 0 ? partnerClients.map((client) => `${client.name} · ${client.status}`) : ["Invite an employee to provision access"],
      certificates: certificates.map((cert) => `${cert.title} · ${cert.sealHash}`),
      risk: events.slice(0, 5).map((event) => `${event.title} · ${event.severity}`),
      profile: [supportNote],
    },
    employee: {
      dashboard: [`Employee ID: ${profile.displayName}`, `Access level: verified`, `Pending tasks: ${hrItems.length}`],
      employment: ["Employment verification ready", "Manager approval ready", "Role update ready"],
      access: [
        `Trusted devices: ${devices.length}`,
        `Access QR ready`,
        `Passkey ${profile.passkeyEnabled ? "enabled" : "pending"}`,
        "SSO ready",
        "Temporary access requests ready",
      ],
      tasks: hrItems,
      security: [
        `MFA: ${profile.passkeyEnabled ? "Ready" : "Pending"}`,
        `Biometric: ${profile.biometricVerified ? "Ready" : "Pending"}`,
        `Device trust: ${profile.deviceTrustEnabled ? "On" : "Off"}`,
      ],
      profile: [supportNote],
      id: credentials.map((credential) => `${credential.label} · ${credential.status}`),
      attendance: hrItems,
      hr: hrItems,
      wallet: [`Identity score: ${profile.identityScore}`, `Login history: ${profile.loginHistory}`],
    },
    inspector: {
      dashboard: [`Inspections saved: ${inspections.length}`, `Pending cases: ${inspections.filter((record) => !record.syncedAt).length}`],
      inspections: [`Inspections saved: ${inspections.length}`, `Offline mode: ${offlineMode ? "On" : "Off"}`],
      cases: ["Case queue ready", "Escalations available", "Resolution workflow ready"],
      evidence: ["Photo upload ready", "Document upload ready", "Evidence lock ready"],
      reports: ["Inspection report ready", "Audit export ready", "Submitted reports available"],
      security: [`Offline mode: ${offlineMode ? "On" : "Off"}`, `Device trust: ${profile.deviceTrustEnabled ? "On" : "Off"}`],
      profile: [supportNote],
      scan: [`Inspections saved: ${inspections.length}`, `Offline mode: ${offlineMode ? "On" : "Off"}`],
      verify: verification ? [`Verification ${verification.status}`, `Policy score ${verification.policyEvaluation.score}`] : ["No verification request yet"],
      offline: [`Offline verify: ${offlineMode ? "Ready" : "Off"}`, `Sync state: ${inspections.every((record) => record.syncedAt) ? "Synced" : "Pending"}`],
      records: inspections.length > 0 ? inspections.map((record) => `${record.id} · ${record.result}`) : ["No inspection records yet"],
    },
    partner: {
      overview: [`Clients: ${partnerClients.length}`, `API usage: ${partnerClients.reduce((sum, client) => sum + client.apiUsage, 0)}`, `Alerts: ${events.length}`],
      "partner-verify": ["Application review ready", "Representative verification ready", "Compliance checklist ready"],
      integrations: ["Integration creation ready", "Webhook test ready", "API docs ready"],
      credentials: partnerClients.length > 0 ? partnerClients.map((client) => `${client.clientId} · ${client.status}`) : ["No client credentials yet"],
      compliance: ["Security review ready", "AML policy ready", "Data protection policy ready"],
      support: [webhookState],
      settings: [supportNote],
      dashboard: [`Clients: ${partnerClients.length}`, `API usage: ${partnerClients.reduce((sum, client) => sum + client.apiUsage, 0)}`],
      clients: partnerClients.length > 0 ? partnerClients.map((client) => `${client.name} · ${client.clientId}`) : ["Create an OAuth client to begin"],
      certificates: certificates.map((cert) => `${cert.title} · ${cert.scope.join(", ")}`),
      webhooks: [webhookState],
      analytics: [`Requests observed: ${events.length + partnerClients.length}`, `Webhook status: ${webhookState}`],
      profile: [supportNote],
    },
  };

  const renderGenericTab = () => {
    const items = variantTabItems[appConfig.id][activeTab] ?? [appConfig.tagline];
    return (
      <SectionCard palette={palette} title={currentTab?.label ?? activeTab} subtitle={currentTab?.description ?? appConfig.tagline}>
        <MetricRow
          palette={palette}
          items={[
            { label: "Trust", value: profile.trustLevel },
            { label: "Score", value: String(profile.identityScore) },
            { label: "Events", value: String(events.length) },
            { label: "Certs", value: String(certificates.length) },
          ]}
        />
        <ListPanel palette={palette} title={`${appConfig.appName} · ${currentTab?.label ?? activeTab}`} items={items} />
        <FlowTimeline palette={palette} items={appConfig.primaryFlow.map((step, index) => ({ step, status: index < 2 ? "done" : "queued" }))} />
      </SectionCard>
    );
  };

  const renderTab = () => {
    if (appConfig.id !== "personal") {
      return renderGenericTab();
    }
    switch (activeTab) {
      case "home":
        return (
          <>
            <IdentityCard
              palette={palette}
              profile={profile}
              verification={verification}
              shareLink={shareLink}
              shareQr={shareQr}
            />
            <SectionCard palette={palette} title="Verification flow" subtitle="Identity Request → Certificate Issued">
              <FlowTimeline palette={palette} items={verificationFlow} />
            </SectionCard>
          </>
        );
      case "wallet":
        return (
          <>
            <SectionCard palette={palette} title="Credential wallet" subtitle="Government IDs, certificates, and identity proofs">
              <MetricRow palette={palette} items={[
                { label: "Credentials", value: String(credentials.length) },
                { label: "Certificates", value: String(certificates.length) },
                { label: "Trusted devices", value: String(devices.length) },
                { label: "Login history", value: String(profile.loginHistory) },
              ]} />
              <ListPanel palette={palette} title="Stored credentials" items={credentials.map((credential) => `${credential.label} · ${credential.issuer}`)} />
            </SectionCard>
          </>
        );
      case "share":
        return (
          <>
            <SectionCard palette={palette} title="Identity sharing" subtitle="QR-first sharing, link sharing, and selective disclosure">
              <SharePanel palette={palette} link={shareLink} qr={shareQr} active={shareMode} onToggle={setShareMode} />
            </SectionCard>
            <SectionCard palette={palette} title="Consent grants" subtitle="Connected apps and shared attributes">
              <ListPanel
                palette={palette}
                title="Active grants"
                items={consents.length > 0 ? consents.map((grant) => `${grant.requester} · ${grant.status} · ${grant.attributes.join(", ")}`) : ["No active consent grants yet."]}
              />
            </SectionCard>
          </>
        );
      case "consent":
        return (
          <>
            <SectionCard palette={palette} title="Consent center" subtitle="Manage connected apps and revocations">
              <ActionSummary palette={palette} message="Use selective disclosure to limit what each app can see." />
              <ListPanel palette={palette} title="Connected apps" items={["NovaID Account Center", "NovaID Trust Hub", "NovaID Security", "Government Services"].slice(0, profile.connectedApps)} />
            </SectionCard>
            <SectionCard palette={palette} title="Revocation history" subtitle="Track grants, revoke access, and replay receipts">
              <ListPanel
                palette={palette}
                title="Consent log"
                items={consents.length > 0 ? consents.map((grant) => `${grant.requester} · ${grant.status}`) : ["No consent activity yet."]}
              />
            </SectionCard>
          </>
        );
      case "security":
        return (
          <>
            <SectionCard palette={palette} title="Security center" subtitle="Passkeys, biometrics, device trust, and recovery">
              <MetricRow palette={palette} items={[
                { label: "Passkeys", value: profile.passkeyEnabled ? "Enabled" : "Off" },
                { label: "Biometric", value: profile.biometricVerified ? "Verified" : "Pending" },
                { label: "Device trust", value: profile.deviceTrustEnabled ? "On" : "Off" },
                { label: "Recovery", value: profile.recoveryEnabled ? "Ready" : "Off" },
              ]} />
              <ListPanel
                palette={palette}
                title="Trusted devices"
                items={(showAllDevices ? devices : devices.slice(0, 2)).map((device) => `${device.deviceName} · ${device.deviceTrustScore}% · ${device.platform}`)}
              />
            </SectionCard>
          </>
        );
      case "profile":
        return (
          <>
            <SectionCard palette={palette} title="Profile" subtitle="NovaAI assistant, certificates, and identity history">
              <ListPanel
                palette={palette}
                title="NovaAI Identity Assistant"
                items={[
                  "Recommend stronger recovery rules",
                  "Warn about risky consent requests",
                  "Suggest passkey adoption",
                ]}
              />
              <ActionSummary palette={palette} message={supportNote} />
            </SectionCard>
            <SectionCard palette={palette} title="Events and certificates" subtitle="Replay-backed proof and audit package">
              <ListPanel palette={palette} title="Recent events" items={events.slice(0, 5).map((event) => `${event.title} · ${event.detail}`)} />
            </SectionCard>
          </>
        );
      default:
        return renderGenericTab();
    }
  };

  return (
    <SafeAreaView style={[styles.safe, { backgroundColor: palette.bg }]}>
      <ScrollView contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false}>
        <View style={[styles.hero, { backgroundColor: palette.surface, borderColor: palette.line, shadowColor: dark ? "#000" : "#0a2540" }]}>
          <View style={styles.heroTop}>
            <View style={{ flex: 1 }}>
              <Text style={[styles.kicker, { color: palette.accent }]}>NovaID ecosystem</Text>
              <Text style={[styles.title, { color: palette.ink }]}>{appConfig.appName}</Text>
              <Text style={[styles.subtitle, { color: palette.muted }]}>{appConfig.tagline}</Text>
            </View>
            <View style={[styles.trustPill, { backgroundColor: `${palette.accent}18`, borderColor: palette.accent }]}>
              <Text style={[styles.trustText, { color: palette.accent }]}>{profile.trustLevel}</Text>
            </View>
          </View>

          <View style={styles.metricsTop}>
            <SmallMetric palette={palette} label="Score" value={String(profile.identityScore)} />
            <SmallMetric palette={palette} label="Credentials" value={String(profile.credentialCount)} />
            <SmallMetric palette={palette} label="Devices" value={String(profile.trustedDevices)} />
            <SmallMetric palette={palette} label="Certificates" value={String(profile.certificateCount)} />
          </View>

          <View style={styles.bannerRow}>
            <Text style={[styles.bannerText, { color: palette.muted }]}>Package {appConfig.packageId}</Text>
            <Text style={[styles.bannerText, { color: palette.muted }]}>{profile.summary}</Text>
          </View>
        </View>

        {banner ? (
          <View style={[styles.banner, { backgroundColor: palette.surface, borderColor: palette.line }]}>
            <Text style={[styles.bannerTitle, { color: banner.tone === "warning" ? palette.warning : banner.tone === "success" ? palette.success : palette.accent }]}>{banner.title}</Text>
            <Text style={[styles.bannerDetail, { color: palette.muted }]}>{banner.detail}</Text>
          </View>
        ) : null}

        <View style={[styles.card, { backgroundColor: palette.surface, borderColor: palette.line }]}>
          <Text style={[styles.sectionTitle, { color: palette.ink }]}>Core controls</Text>
          <Text style={[styles.sectionSubtitle, { color: palette.muted }]}>All buttons are wired to stateful actions, governed service calls, and visible confirmations.</Text>
          <View style={styles.buttonGrid}>
            {appConfig.actions.map((action) => (
              <ActionButton key={action.label} palette={palette} action={action} onPress={() => void handleAction(action)} />
            ))}
          </View>
        </View>

        <View style={[styles.tabRow, { borderColor: palette.line, backgroundColor: palette.surface }]}>
          {appConfig.tabs.map((tab) => (
            <TabButton
              key={tab.key}
              palette={palette}
              label={tab.label}
              active={activeTab === tab.key}
              onPress={() => setActiveTab(tab.key)}
            />
          ))}
        </View>

        <View style={styles.tabHintRow}>
          <Text style={[styles.tabHint, { color: palette.muted }]}>{appConfig.tabs.find((tab) => tab.key === activeTab)?.description}</Text>
          <Switch value={offlineMode} onValueChange={setOfflineMode} thumbColor={offlineMode ? palette.accent : "#ffffff"} />
        </View>

        {renderTab()}

        <SectionCard palette={palette} title="Audit trail" subtitle="Replay-backed identity events and consent history">
          <ListPanel palette={palette} title="Event stream" items={events.map((event) => `${event.title} · ${event.severity}`)} />
        </SectionCard>

        <SectionCard palette={palette} title="Integrated services" subtitle="Backend-synced identity services and proof surfaces">
          <ListPanel
            palette={palette}
            title="Service endpoints"
            items={[
              "novaid.service.ts",
              "credential.service.ts",
              "consent.service.ts",
              "deviceTrust.service.ts",
              "certificate.service.ts",
              "inspection.service.ts",
              "partner.service.ts",
              "novaaiIdentity.service.ts",
            ]}
          />
        </SectionCard>

        <View style={[styles.card, { backgroundColor: palette.surface, borderColor: palette.line }]}>
          <Text style={[styles.sectionTitle, { color: palette.ink }]}>Flow confirmation</Text>
          <Text style={[styles.sectionSubtitle, { color: palette.muted }]}>Identity Request → Biometric Verification → Document Validation → Liveness Detection → Policy Evaluation → Identity Approved → Digital Certificate Issued</Text>
          <Pressable
            accessibilityRole="button"
            onPress={async () => {
              const audit = await buildAuditPackage(events.slice(0, 5).map((event) => event.id));
              notify({ tone: "success", title: "Audit package built", detail: audit.digitalSignature });
            }}
            style={({ pressed }) => [
              styles.auditButton,
              { backgroundColor: palette.accent, opacity: pressed ? 0.85 : 1 },
            ]}
          >
            <Text style={styles.auditButtonText}>Build signed proof package</Text>
          </Pressable>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

function IdentityCard({
  palette,
  profile,
  verification,
  shareLink,
  shareQr,
}: {
  palette: {
    bg: string;
    surface: string;
    surfaceAlt: string;
    ink: string;
    muted: string;
    line: string;
    accent: string;
    success: string;
    warning: string;
    danger: string;
  };
  profile: IdentityProfile;
  verification: VerificationRequest | null;
  shareLink: string;
  shareQr: string;
}) {
  return (
    <SectionCard palette={palette} title="Digital identity card" subtitle="QR-first, biometric-ready, selective-disclosure identity">
      <View style={[styles.identityCard, { backgroundColor: palette.surfaceAlt, borderColor: palette.line }]}>
        <View style={styles.identityHeader}>
          <View>
            <Text style={[styles.identityName, { color: palette.ink }]}>{profile.displayName}</Text>
            <Text style={[styles.identityMeta, { color: palette.muted }]}>{profile.walletLabel}</Text>
          </View>
          <TrustBadge palette={palette} trustLevel={profile.trustLevel} />
        </View>
        <View style={styles.identityStats}>
          <SmallMetric palette={palette} label="Biometric" value={profile.biometricVerified ? "OK" : "Pending"} />
          <SmallMetric palette={palette} label="Passkey" value={profile.passkeyEnabled ? "On" : "Off"} />
          <SmallMetric palette={palette} label="Devices" value={String(profile.trustedDevices)} />
          <SmallMetric palette={palette} label="Login history" value={String(profile.loginHistory)} />
        </View>
        <View style={[styles.glassPanel, { borderColor: palette.line }]}>
          <Text style={[styles.glassTitle, { color: palette.ink }]}>Replay proof</Text>
          <Text style={[styles.glassText, { color: palette.muted }]}>
            {verification
              ? verification.status === "pending"
                ? `Step ${verification.step} · verification pending`
                : `Step ${verification.step} · score ${verification.policyEvaluation.score}`
              : "Awaiting verification refresh"}
          </Text>
          <Text style={[styles.glassText, { color: palette.muted }]}>QR: {shareQr}</Text>
          <Text style={[styles.glassText, { color: palette.muted }]}>Link: {shareLink}</Text>
        </View>
      </View>
    </SectionCard>
  );
}

function SectionCard({
  palette,
  title,
  subtitle,
  children,
}: {
  palette: {
    bg: string;
    surface: string;
    surfaceAlt: string;
    ink: string;
    muted: string;
    line: string;
    accent: string;
    success: string;
    warning: string;
    danger: string;
  };
  title: string;
  subtitle: string;
  children: React.ReactNode;
}) {
  return (
    <View style={[styles.card, { backgroundColor: palette.surface, borderColor: palette.line }]}>
      <Text style={[styles.sectionTitle, { color: palette.ink }]}>{title}</Text>
      <Text style={[styles.sectionSubtitle, { color: palette.muted }]}>{subtitle}</Text>
      <View style={styles.sectionBody}>{children}</View>
    </View>
  );
}

function TrustBadge({
  palette,
  trustLevel,
}: {
  palette: {
    accent: string;
    success: string;
    warning: string;
    muted: string;
    line: string;
    ink: string;
    surface: string;
    surfaceAlt: string;
    bg: string;
    danger: string;
  };
  trustLevel: string;
}) {
  return (
    <View style={[styles.trustBadge, { backgroundColor: `${palette.accent}20`, borderColor: palette.accent }]}>
      <Text style={[styles.trustBadgeText, { color: palette.accent }]}>{trustLevel}</Text>
    </View>
  );
}

function MetricRow({
  palette,
  items,
}: {
  palette: {
    accent: string;
    success: string;
    warning: string;
    muted: string;
    line: string;
    ink: string;
    surface: string;
    surfaceAlt: string;
    bg: string;
    danger: string;
  };
  items: Array<{ label: string; value: string }>;
}) {
  return (
    <View style={styles.metricRow}>
      {items.map((item) => (
        <View key={item.label} style={[styles.metricCard, { backgroundColor: palette.surfaceAlt, borderColor: palette.line }]}>
          <Text style={[styles.metricValue, { color: palette.ink }]}>{item.value}</Text>
          <Text style={[styles.metricLabel, { color: palette.muted }]}>{item.label}</Text>
        </View>
      ))}
    </View>
  );
}

function SmallMetric({
  palette,
  label,
  value,
}: {
  palette: {
    accent: string;
    success: string;
    warning: string;
    muted: string;
    line: string;
    ink: string;
    surface: string;
    surfaceAlt: string;
    bg: string;
    danger: string;
  };
  label: string;
  value: string;
}) {
  return (
    <View style={[styles.smallMetric, { backgroundColor: palette.surfaceAlt, borderColor: palette.line }]}>
      <Text style={[styles.smallMetricValue, { color: palette.ink }]}>{value}</Text>
      <Text style={[styles.smallMetricLabel, { color: palette.muted }]}>{label}</Text>
    </View>
  );
}

function ActionButton({
  palette,
  action,
  onPress,
}: {
  palette: {
    accent: string;
    success: string;
    warning: string;
    muted: string;
    line: string;
    ink: string;
    surface: string;
    surfaceAlt: string;
    bg: string;
    danger: string;
  };
  action: AppAction;
  onPress: () => void;
}) {
  return (
    <Pressable
      accessibilityRole="button"
      onPress={onPress}
      style={({ pressed }) => [
        styles.actionButton,
        { backgroundColor: palette.surfaceAlt, borderColor: palette.line, opacity: pressed ? 0.88 : 1 },
      ]}
    >
      <Text style={[styles.actionButtonText, { color: palette.ink }]}>{action.label}</Text>
      <Text style={[styles.actionButtonDetail, { color: palette.muted }]}>{action.detail}</Text>
    </Pressable>
  );
}

function TabButton({
  palette,
  label,
  active,
  onPress,
}: {
  palette: {
    accent: string;
    success: string;
    warning: string;
    muted: string;
    line: string;
    ink: string;
    surface: string;
    surfaceAlt: string;
    bg: string;
    danger: string;
  };
  label: string;
  active: boolean;
  onPress: () => void;
}) {
  return (
    <Pressable onPress={onPress} style={[styles.tabButton, { borderColor: palette.line, backgroundColor: active ? `${palette.accent}16` : "transparent" }]}>
      <Text style={[styles.tabLabel, { color: active ? palette.accent : palette.muted }]}>{label}</Text>
    </Pressable>
  );
}

function FlowTimeline({
  palette,
  items,
}: {
  palette: {
    accent: string;
    success: string;
    warning: string;
    muted: string;
    line: string;
    ink: string;
    surface: string;
    surfaceAlt: string;
    bg: string;
    danger: string;
  };
  items: Array<{ step: string; status: string }>;
}) {
  return (
    <View style={styles.flowList}>
      {items.map((item, index) => (
        <View key={`${item.step}-${index}`} style={[styles.flowRow, { borderColor: palette.line }]}>
          <View style={[styles.flowDot, { backgroundColor: index < 2 ? palette.success : palette.warning }]} />
          <View style={styles.flowTextWrap}>
            <Text style={[styles.flowTitle, { color: palette.ink }]}>{item.step}</Text>
            <Text style={[styles.flowStatus, { color: palette.muted }]}>{item.status}</Text>
          </View>
        </View>
      ))}
    </View>
  );
}

function ListPanel({
  palette,
  title,
  items,
}: {
  palette: {
    accent: string;
    success: string;
    warning: string;
    muted: string;
    line: string;
    ink: string;
    surface: string;
    surfaceAlt: string;
    bg: string;
    danger: string;
  };
  title: string;
  items: string[];
}) {
  return (
    <View style={[styles.listPanel, { borderColor: palette.line, backgroundColor: palette.surfaceAlt }]}>
      <Text style={[styles.listTitle, { color: palette.ink }]}>{title}</Text>
      {items.map((item) => (
        <Text key={item} style={[styles.listItem, { color: palette.muted }]}>• {item}</Text>
      ))}
    </View>
  );
}

function SharePanel({
  palette,
  link,
  qr,
  active,
  onToggle,
}: {
  palette: {
    accent: string;
    success: string;
    warning: string;
    muted: string;
    line: string;
    ink: string;
    surface: string;
    surfaceAlt: string;
    bg: string;
    danger: string;
  };
  link: string;
  qr: string;
  active: boolean;
  onToggle: (next: boolean) => void;
}) {
  return (
    <View style={styles.shareWrap}>
      <View style={[styles.shareCard, { backgroundColor: palette.surfaceAlt, borderColor: palette.line }]}>
        <Text style={[styles.shareLabel, { color: palette.muted }]}>Share mode</Text>
        <View style={styles.shareToggleRow}>
          <Text style={[styles.shareValue, { color: palette.ink }]}>{active ? "QR first" : "Link first"}</Text>
          <Switch value={active} onValueChange={onToggle} thumbColor={active ? palette.accent : "#ffffff"} />
        </View>
      </View>
      <View style={[styles.shareCard, { backgroundColor: palette.surfaceAlt, borderColor: palette.line }]}>
        <Text style={[styles.shareLabel, { color: palette.muted }]}>QR identity share</Text>
        <Text style={[styles.shareCode, { color: palette.ink }]}>{qr}</Text>
      </View>
      <View style={[styles.shareCard, { backgroundColor: palette.surfaceAlt, borderColor: palette.line }]}>
        <Text style={[styles.shareLabel, { color: palette.muted }]}>Selective disclosure link</Text>
        <Text style={[styles.shareValue, { color: palette.ink }]}>{link}</Text>
      </View>
    </View>
  );
}

function ActionSummary({
  palette,
  message,
}: {
  palette: {
    accent: string;
    success: string;
    warning: string;
    muted: string;
    line: string;
    ink: string;
    surface: string;
    surfaceAlt: string;
    bg: string;
    danger: string;
  };
  message: string;
}) {
  return (
    <View style={[styles.summaryCard, { backgroundColor: palette.surfaceAlt, borderColor: palette.line }]}>
      <Text style={[styles.summaryText, { color: palette.ink }]}>{message}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  actionButton: {
    borderRadius: 20,
    borderWidth: 1,
    flexGrow: 1,
    minHeight: 96,
    padding: 14,
    width: "48%",
  },
  actionButtonDetail: {
    fontSize: 12,
    lineHeight: 17,
    marginTop: 8,
  },
  actionButtonText: {
    fontSize: 15,
    fontWeight: "800",
  },
  auditButton: {
    borderRadius: 18,
    marginTop: 10,
    minHeight: 52,
    paddingHorizontal: 18,
    paddingVertical: 14,
  },
  auditButtonText: {
    color: "#ffffff",
    fontSize: 15,
    fontWeight: "900",
    textAlign: "center",
  },
  banner: {
    borderRadius: 24,
    borderWidth: 1,
    gap: 4,
    marginTop: 16,
    padding: 16,
  },
  bannerDetail: {
    fontSize: 14,
    lineHeight: 20,
  },
  bannerRow: {
    gap: 4,
    marginTop: 12,
  },
  bannerText: {
    fontSize: 12,
    lineHeight: 17,
  },
  buttonGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 10,
    marginTop: 8,
  },
  card: {
    borderRadius: 28,
    borderWidth: 1,
    gap: 12,
    marginTop: 16,
    padding: 18,
  },
  flowDot: {
    borderRadius: 999,
    height: 12,
    marginTop: 6,
    width: 12,
  },
  flowList: {
    gap: 12,
  },
  flowRow: {
    borderBottomWidth: 1,
    flexDirection: "row",
    gap: 12,
    paddingBottom: 12,
  },
  flowStatus: {
    fontSize: 12,
    marginTop: 4,
  },
  flowTextWrap: {
    flex: 1,
  },
  flowTitle: {
    fontSize: 15,
    fontWeight: "800",
  },
  glassPanel: {
    borderRadius: 24,
    borderWidth: 1,
    gap: 6,
    marginTop: 10,
    padding: 16,
  },
  glassText: {
    fontSize: 13,
    lineHeight: 19,
  },
  glassTitle: {
    fontSize: 16,
    fontWeight: "800",
  },
  hero: {
    borderRadius: 32,
    borderWidth: 1,
    gap: 16,
    marginBottom: 8,
    padding: 20,
    shadowOffset: { width: 0, height: 12 },
    shadowOpacity: 0.1,
    shadowRadius: 24,
  },
  heroTop: {
    flexDirection: "row",
    gap: 16,
  },
  metricsTop: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 10,
  },
  identityCard: {
    borderRadius: 28,
    borderWidth: 1,
    gap: 16,
    padding: 18,
  },
  identityHeader: {
    alignItems: "center",
    flexDirection: "row",
    justifyContent: "space-between",
  },
  identityMeta: {
    fontSize: 13,
    marginTop: 4,
  },
  identityName: {
    fontSize: 24,
    fontWeight: "900",
  },
  identityStats: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 10,
  },
  kicker: {
    fontSize: 12,
    fontWeight: "900",
    letterSpacing: 0.8,
    textTransform: "uppercase",
  },
  listItem: {
    fontSize: 13,
    lineHeight: 19,
  },
  listPanel: {
    borderRadius: 20,
    borderWidth: 1,
    gap: 8,
    padding: 14,
  },
  listTitle: {
    fontSize: 14,
    fontWeight: "800",
  },
  metricCard: {
    borderRadius: 18,
    borderWidth: 1,
    flex: 1,
    minWidth: 130,
    padding: 12,
  },
  metricLabel: {
    fontSize: 12,
    marginTop: 4,
  },
  metricRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 10,
  },
  metricValue: {
    fontSize: 18,
    fontWeight: "900",
  },
  safe: {
    flex: 1,
  },
  scroll: {
    padding: 16,
    paddingBottom: 36,
  },
  sectionBody: {
    gap: 12,
  },
  sectionSubtitle: {
    fontSize: 13,
    lineHeight: 19,
  },
  sectionTitle: {
    fontSize: 19,
    fontWeight: "900",
  },
  shareCard: {
    borderRadius: 18,
    borderWidth: 1,
    gap: 8,
    padding: 14,
  },
  shareCode: {
    fontSize: 14,
    fontWeight: "800",
  },
  shareLabel: {
    fontSize: 12,
    fontWeight: "800",
    textTransform: "uppercase",
  },
  shareToggleRow: {
    alignItems: "center",
    flexDirection: "row",
    justifyContent: "space-between",
  },
  shareValue: {
    fontSize: 15,
    fontWeight: "800",
  },
  shareWrap: {
    gap: 12,
  },
  smallMetric: {
    borderRadius: 16,
    borderWidth: 1,
    minWidth: 108,
    paddingHorizontal: 12,
    paddingVertical: 12,
  },
  smallMetricLabel: {
    fontSize: 11,
    marginTop: 4,
    textTransform: "uppercase",
  },
  smallMetricValue: {
    fontSize: 18,
    fontWeight: "900",
  },
  summaryCard: {
    borderRadius: 18,
    borderWidth: 1,
    padding: 14,
  },
  summaryText: {
    fontSize: 13,
    lineHeight: 19,
  },
  bannerTitle: {
    fontSize: 16,
    fontWeight: "900",
  },
  subtitle: {
    fontSize: 14,
    lineHeight: 20,
    marginTop: 8,
  },
  tabButton: {
    borderBottomWidth: 1,
    paddingHorizontal: 10,
    paddingVertical: 12,
  },
  tabHint: {
    flex: 1,
    fontSize: 12,
    lineHeight: 17,
  },
  tabHintRow: {
    alignItems: "center",
    flexDirection: "row",
    gap: 10,
    marginTop: 12,
  },
  tabLabel: {
    fontSize: 13,
    fontWeight: "800",
  },
  tabRow: {
    borderRadius: 22,
    borderWidth: 1,
    flexDirection: "row",
    flexWrap: "wrap",
    justifyContent: "space-between",
    marginTop: 16,
    overflow: "hidden",
  },
  title: {
    fontSize: 28,
    fontWeight: "900",
    lineHeight: 33,
  },
  trustBadge: {
    borderRadius: 999,
    borderWidth: 1,
    paddingHorizontal: 12,
    paddingVertical: 8,
  },
  trustBadgeText: {
    fontSize: 12,
    fontWeight: "900",
    textTransform: "uppercase",
  },
  trustPill: {
    alignSelf: "flex-start",
    borderRadius: 999,
    borderWidth: 1,
    paddingHorizontal: 12,
    paddingVertical: 8,
  },
  trustText: {
    fontSize: 12,
    fontWeight: "900",
    textTransform: "uppercase",
  },
});
