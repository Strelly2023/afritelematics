type GlobalRuntime = {
  locale: string;
  source: "fallback" | "cache" | "network";
  region: {
    region_id: string;
    currency: string;
    currency_minor_digits: number;
    time_zone: string;
  };
  brand: {
    name: string;
    short_name: string;
    primary_color: string;
    logo_url?: string | null;
  };
  t(key: string): string;
  money(minor: number): string;
  localTime(value: string | number | Date): string;
};

export function useGlobalRuntime(
  apiRequest: <T>(path: string, options?: any) => Promise<T>,
  organizationId: string,
  regionId: string,
  requestedLocale?: string,
): GlobalRuntime;
