import { PromptRunResponse } from "../types";

type Props = {
  run: PromptRunResponse | null;
};

export default function ValidatorPanel({ run }: Props) {
  return (
    <div className="card">
      <h2>Validator Swarm</h2>
      {!run ? (
        <p>No run yet.</p>
      ) : (
        <>
          <div className="run-summary">
            <p><strong>Run ID:</strong> {run.run_id}</p>
            <p><strong>Status:</strong> {run.final_status}</p>
            <p><strong>Total Cost:</strong> {run.total_cost_usdc} USDC</p>
            <p><strong>Validator Count:</strong> {run.validator_count}</p>
          </div>

          <div className="validator-list">
            {run.results.map((item) => (
              <div className="validator-card" key={item.validator_id + item.check_type}>
                <h3>{item.check_type}</h3>
                <p><strong>Status:</strong> {item.status}</p>
                <p><strong>Risk:</strong> {item.risk_score}</p>
                <p><strong>Reason:</strong> {item.reason}</p>
                <p><strong>Latency:</strong> {item.response_time_ms} ms</p>
                <p><strong>Price:</strong> {item.unit_price} USDC</p>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
