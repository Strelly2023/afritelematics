import { useEffect, useState } from "react";

import { getOperatorDashboard } from "../../core/api/operator.service";
import type { OperatorDashboard } from "../../core/models/operator";

type OperatorDashboardState = {
  dashboard: OperatorDashboard | null;
  loading: boolean;
  error: string;
};

export function useOperatorDashboard() {
  const [state, setState] = useState<OperatorDashboardState>({
    dashboard: null,
    loading: false,
    error: "",
  });

  async function refreshDashboard() {
    setState((current) => ({ ...current, loading: true, error: "" }));

    try {
      const dashboard = await getOperatorDashboard();
      setState({
        dashboard,
        loading: false,
        error: "",
      });
    } catch (error) {
      setState((current) => ({
        ...current,
        loading: false,
        error:
          error instanceof Error
            ? error.message
            : "operator_dashboard_unavailable",
      }));
    }
  }

  useEffect(() => {
    void refreshDashboard();
  }, []);

  return {
    ...state,
    refreshDashboard,
  };
}
