import AsyncStorage from "@react-native-async-storage/async-storage";
import { useEffect, useMemo, useState } from "react";

const CACHE_KEY = "@afriride/global-config/v1";
const MESSAGES = {
  en: {
    "app.rider": "Rider",
    "app.driver": "Driver",
    "nav.home": "Home",
    "nav.trips": "Trips",
    "nav.wallet": "Wallet",
    "nav.activity": "Activity",
    "nav.profile": "Profile",
    "nav.earnings": "Earnings",
    "nav.trust": "Trust",
    "mode.pilot": "Pilot",
    "mode.live": "Live",
  },
  sw: {
    "app.rider": "Abiria",
    "app.driver": "Dereva",
    "nav.home": "Nyumbani",
    "nav.trips": "Safari",
    "nav.wallet": "Pochi",
    "nav.activity": "Shughuli",
    "nav.profile": "Wasifu",
    "nav.earnings": "Mapato",
    "nav.trust": "Uaminifu",
    "mode.pilot": "Majaribio",
    "mode.live": "Moja kwa moja",
  },
  zu: {
    "app.rider": "Umgibeli",
    "app.driver": "Umshayeli",
    "nav.home": "Ikhaya",
    "nav.trips": "Uhambo",
    "nav.wallet": "Isikhwama",
    "nav.activity": "Umsebenzi",
    "nav.profile": "Iphrofayela",
    "nav.earnings": "Imali",
    "nav.trust": "Ukwethembeka",
    "mode.pilot": "Ukuhlola",
    "mode.live": "Bukhoma",
  },
};

const FALLBACK = {
  locale: "en-UG",
  region: {
    region_id: "ug-kla",
    currency: "UGX",
    currency_minor_digits: 0,
    time_zone: "Africa/Kampala",
  },
  brand: {
    name: "AfriRide",
    short_name: "AfriRide",
    primary_color: "#006B57",
  },
};

export function useGlobalRuntime(apiRequest, organizationId, regionId, requestedLocale) {
  const [config, setConfig] = useState(FALLBACK);
  const [source, setSource] = useState("fallback");
  useEffect(() => {
    let active = true;
    void (async () => {
      const cached = await AsyncStorage.getItem(`${CACHE_KEY}:${organizationId}:${regionId}`);
      if (cached && active) {
        try {
          setConfig(JSON.parse(cached));
          setSource("cache");
        } catch {
          await AsyncStorage.removeItem(`${CACHE_KEY}:${organizationId}:${regionId}`);
        }
      }
      try {
        const query = new URLSearchParams({
          region_id: regionId,
          ...(requestedLocale ? { locale: requestedLocale } : {}),
        });
        const fresh = await apiRequest(`/v1/global/config?${query.toString()}`, {
          headers: { "X-Organization-ID": organizationId },
        });
        await AsyncStorage.setItem(
          `${CACHE_KEY}:${organizationId}:${regionId}`,
          JSON.stringify(fresh),
        );
        if (active) {
          setConfig(fresh);
          setSource("network");
        }
      } catch {
        // Cached configuration remains authoritative for offline startup.
      }
    })();
    return () => {
      active = false;
    };
  }, [apiRequest, organizationId, regionId, requestedLocale]);

  const language = String(config.locale || "en").split("-")[0];
  const messages = MESSAGES[language] || MESSAGES.en;
  return useMemo(
    () => ({
      ...config,
      source,
      t: (key) => messages[key] || MESSAGES.en[key] || key,
      money: (minor) =>
        new Intl.NumberFormat(config.locale, {
          style: "currency",
          currency: config.region.currency,
          minimumFractionDigits: config.region.currency_minor_digits,
          maximumFractionDigits: config.region.currency_minor_digits,
        }).format(minor / 10 ** config.region.currency_minor_digits),
      localTime: (value) =>
        new Intl.DateTimeFormat(config.locale, {
          dateStyle: "medium",
          timeStyle: "short",
          timeZone: config.region.time_zone,
        }).format(new Date(value)),
    }),
    [config, messages, source],
  );
}
