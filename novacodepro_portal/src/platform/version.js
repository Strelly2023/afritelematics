const FALLBACK_BUILD_INFO = {
  application: "NovaCodePro Portal",
  version: "0.1.0",
  build_id: "local-dev",
  commit: "unknown",
  built_at: "unknown",
  api_base_url: "/v1",
};

export const NOVACODEPRO_BUILD_INFO =
  typeof __NOVACODEPRO_BUILD_INFO__ !== "undefined" ? __NOVACODEPRO_BUILD_INFO__ : FALLBACK_BUILD_INFO;

