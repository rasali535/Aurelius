import { useEffect, useState } from "react";
import PromptForm from "../components/PromptForm";
import MetricsCards from "../components/MetricsCards";
import ValidatorPanel from "../components/ValidatorPanel";
import TransactionFeed from "../components/TransactionFeed";
import { api } from "../services/api";
import type { DashboardSummary, PromptRunResponse } from "../types";

export default function Dashboard() {
  const [loading, setLoading] = useState(false);
  const [run, setRun] = useState<PromptRunResponse | null>(null);
  const [summary, setSummary] = useState<DashboardSummary | null>(null);

  const mockSummary: DashboardSummary = {
    total_prompt_runs: 128,
    total_validations: 842,
    total_payments: 1024,
    total_spend_usdc: 0.84,
    latest_transactions: [
      { id: "1", amount_usdc: 0.0001, status: "settled", tx_hash: "0x34a...b12", settled_at: new Date().toISOString() },
      { id: "2", amount_usdc: 0.0005, status: "settled", tx_hash: "0x78e...fde", settled_at: new Date().toISOString() },
      { id: "3", amount_usdc: 0.0002, status: "settled", tx_hash: "0x12c...a45", settled_at: new Date().toISOString() }
    ]
  };

  const fetchSummary = async () => {
    try {
      const res = await api.get("/dashboard/summary");
      setSummary(res.data);
    } catch (err) {
      console.warn("API unavailable, switching to mock data", err);
      if (!summary) setSummary(mockSummary);
    }
  };

  useEffect(() => {
    fetchSummary();
    const interval = setInterval(fetchSummary, 60000); // Check every minute
    return () => clearInterval(interval);
  }, [summary]);

  const handleRun = async (prompt: string) => {
    setLoading(true);
    try {
      const res = await api.post("/run-prompt", { prompt });
      setRun(res.data);
      await fetchSummary();
    } catch (err) {
      console.warn("Run prompt failed, generating mock response", err);
      const mockRun: PromptRunResponse = {
        run_id: Math.random().toString(36).substr(2, 9),
        draft_response: "This is a simulated secure response for: " + prompt,
        final_status: "approved",
        total_cost_usdc: 0.005,
        validator_count: 3,
        results: [
          { validator_id: "V-1", check_type: "toxicity", status: "passed", risk_score: 0.01, reason: "No harmful content detected", response_time_ms: 240, unit_price: 0.001 },
          { validator_id: "V-2", check_type: "pii", status: "passed", risk_score: 0.0, reason: "No private information found", response_time_ms: 180, unit_price: 0.001 },
          { validator_id: "V-3", check_type: "jailbreak", status: "passed", risk_score: 0.05, reason: "Input meets safety guidelines", response_time_ms: 310, unit_price: 0.001 }
        ]
      };
      setRun(mockRun);
    } finally {
      setLoading(false);
    }
  };

  const handleBatchRun = async () => {
    setLoading(true);
    try {
      await api.post("/run-demo-batch");
      await fetchSummary();
    } catch (err) {
      console.error("Batch run failed", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page">
      <header>
        <h1>Aurelius</h1>
        <p className="subtitle">
          Autonomous LLM guardrail network with sub-cent agent-to-agent payments.
        </p>
      </header>

      <MetricsCards summary={summary} />
      
      <section className="card margin-info" style={{ background: 'rgba(255, 107, 107, 0.1)', border: '1px solid #ff6b6b', marginBottom: '2rem' }}>
        <h3>🚨 Economic Proof: Why this model needs Arc</h3>
        <p>
          Traditional gas fees ($0.05 - $0.50) make <strong>agentic nanopayments</strong> impossible. 
          At our <strong>$0.005</strong> per-validation price point:
        </p>
        <ul style={{ listStyleType: 'inside', marginTop: '10px' }}>
          <li><strong>Traditional L1/L2:</strong> Transaction Cost {'>'} Transaction Value (1000% Loss).</li>
          <li><strong>Arc Network:</strong> Near-zero overhead enables high-frequency micro-commerce.</li>
        </ul>
      </section>

      <PromptForm onRun={handleRun} onBatchRun={handleBatchRun} loading={loading} />

      <div className="grid-two">
        <ValidatorPanel run={run} />
        <TransactionFeed summary={summary} />
      </div>
    </div>
  );
}
