export type PassengerIntelligenceFeed = {
  view: "novaride_mobile_passenger_intelligence";
  organization_id: string;
  passenger_id?: string | null;
  system_status: "stable";
  safety_score: number;
  demand: "low" | "moderate" | "high";
  eta_confidence: "medium" | "high";
  alerts: string[];
  trust: {
    driver_verified: boolean;
    vehicle_verified: boolean;
    payment_secure: boolean;
  };
  autonomous_mode?: boolean;
  predictive_positioning?: {
    mode: "held" | "guided" | "fully_autonomous";
    target_zone: string;
    confidence: number;
    instruction: string;
    reason: string;
    projection_only: true;
    read_only: true;
  };
  city_automation?: {
    mode: "city_held" | "city_supervised" | "city_autonomous" | "zero_operator";
    zero_operator_mode: boolean;
    coverage_score: number;
    active_drivers: number;
    active_rides: number;
    city_zones: string[];
    recommended_zone: string;
    instruction: string;
    reason: string;
    prediction: {
      city_zone_count: number;
      city_trust_score: number;
      coverage_score: number;
      demand_level: "low" | "moderate" | "high";
    };
    projection_only: true;
    read_only: true;
  };
  multi_city_orchestration?: {
    mode: "global_held" | "global_supervised" | "global_autonomous" | "global_zero_operator";
    city_count: number;
    active_city_count: number;
    global_coverage_score: number;
    global_trust_score: number;
    instruction: string;
    reason: string;
    prediction: {
      city_count: number;
      active_city_count: number;
      coverage_score: number;
      trust_score: number;
      demand_level: "low" | "moderate" | "high";
    };
    projection_only: true;
    read_only: true;
  };
  digital_twin?: {
    mode: "shadow_sync" | "predictive_closed_loop" | "city_closed_loop" | "global_closed_loop";
    live_sync_score: number;
    twin_health_score: number;
    live_state: {
      active_drivers: number;
      active_rides: number;
      zone: string;
      demand_level: "low" | "moderate" | "high";
      trust_score: number;
      city_coverage_score: number;
      global_coverage_score: number;
    };
    prediction: {
      next_state: string;
      confidence: number;
      trust_score: number;
      evidence_coverage: number;
      exception_pressure: number;
    };
    recommendation: string;
    reason: string;
    projection_only: true;
    read_only: true;
  };
  self_improving_loop?: {
    mode: "watching" | "learning" | "recalibrating";
    cycle: string[];
    band: string;
    trend: {
      count: number;
      first: number;
      latest: number;
      delta: number;
      slope: number;
      direction: "stable" | "rising" | "falling";
      average: number;
      minimum: number;
      maximum: number;
    };
    recommendations: string[];
    recalibration_notes: string[];
    watch_items: string[];
    outcome_score: number;
    measurement_summary: string;
    projection_only: true;
    read_only: true;
  };
  projection_only: true;
  read_only: true;
  created_at: string;
};
