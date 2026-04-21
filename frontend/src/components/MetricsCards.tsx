import type { DashboardSummary } from "../types";

type Props = {
  summary: DashboardSummary | null;
};

export default function MetricsCards({ summary }: Props) {
  return (
    <div className="metrics-column">
      <div className="card metric-tile">
        <div className="tile-glow blue"></div>
        <div className="tile-content">
          <span className="tile-label">PROMPT_SEQUENCE</span>
          <strong className="tile-value">{summary?.total_prompt_runs ?? 0}</strong>
        </div>
      </div>
      
      <div className="card metric-tile">
        <div className="tile-glow purple"></div>
        <div className="tile-content">
          <span className="tile-label">VALIDATION_NODES</span>
          <strong className="tile-value">{summary?.total_validations ?? 0}</strong>
        </div>
      </div>

      <div className="card metric-tile">
        <div className="tile-glow green"></div>
        <div className="tile-content">
          <span className="tile-label">AUTH_SETTLEMENTS</span>
          <strong className="tile-value">{summary?.total_payments ?? 0}</strong>
        </div>
      </div>

      <div className="card metric-tile highlight">
        <div className="tile-glow gold"></div>
        <div className="tile-content">
          <span className="tile-label">ECONOMY_THROUGHPUT</span>
          <strong className="tile-value text-success">
            {summary?.total_spend_usdc?.toFixed(4) ?? "0.0000"} <span style={{ fontSize: '0.8rem', opacity: 0.6 }}>USDC</span>
          </strong>
        </div>
      </div>
    </div>
  );
}
