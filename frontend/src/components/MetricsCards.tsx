import type { DashboardSummary } from "../types";

type Props = {
  summary: DashboardSummary | null;
};

export default function MetricsCards({ summary }: Props) {
  return (
    <div className="metrics-grid">
      <div className="metric-card">
        <span>Prompt Runs</span>
        <strong>{summary?.total_prompt_runs ?? 0}</strong>
      </div>
      <div className="metric-card">
        <span>Validations</span>
        <strong>{summary?.total_validations ?? 0}</strong>
      </div>
      <div className="metric-card">
        <span>Payments</span>
        <strong>{summary?.total_payments ?? 0}</strong>
      </div>
      <div className="metric-card">
        <span>Total Spend (USDC)</span>
        <strong>{summary?.total_spend_usdc?.toFixed(6) ?? "0.000000"}</strong>
      </div>
    </div>
  );
}
