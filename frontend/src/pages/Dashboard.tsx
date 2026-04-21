import { useEffect, useState } from "react";
import PromptForm from "../components/PromptForm";
import MetricsCards from "../components/MetricsCards";
import ValidatorPanel from "../components/ValidatorPanel";
import TransactionFeed from "../components/TransactionFeed";
import { api } from "../services/api";
import type { DashboardSummary, PromptRunResponse } from "../types";

export default function Dashboard({ onBack }: { onBack: () => void }) {
  const [loading, setLoading] = useState(false);
  const [run, setRun] = useState<PromptRunResponse | null>(null);
  const [routerResult, setRouterResult] = useState<any | null>(null);
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [isSimulating, setIsSimulating] = useState(false);

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
    const interval = setInterval(fetchSummary, 3000); 
    return () => clearInterval(interval);
  }, [summary]);

  useEffect(() => {
    let simInterval: any;
    if (isSimulating) {
      simInterval = setInterval(async () => {
        const tasks = [
          "Validate smart contract security",
          "Check PII in user data",
          "Analyze cross-chain arbitrage opportunity",
          "Verify identity of agent V-9",
          "Route transaction to optimal liquidity pool"
        ];
        const randomTask = tasks[Math.floor(Math.random() * tasks.length)];
        handleRouterRun(randomTask);
      }, 8000);
    }
    return () => clearInterval(simInterval);
  }, [isSimulating]);

  const handleRun = async (prompt: string) => {
    setLoading(true);
    setRouterResult(null);
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

  const handleRouterRun = async (task: string) => {
    setLoading(true);
    setRun(null);
    try {
      const res = await api.post("/router/execute", { task });
      setRouterResult(res.data);
      await fetchSummary();
    } catch (err) {
      console.warn("Router execution failed, using mock", err);
      setRouterResult({
        model_id: "meta-llama/Llama-3-70B-Instruct",
        output: "Based on your request, I've analyzed the best path for decentralized identity implementation...",
        price_usdc: 0.0008,
        status: "settled",
        reasoning: "Complex architectural request requiring high reasoning capability."
      });
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
    <div className="page fade-in">
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '48px' }}>
        <div>
          <h1>Aurelius</h1>
          <p className="subtitle" style={{ marginBottom: 0 }}>
            Autonomous AI Infrastructure with Native USDC Value Settlement on Arc.
          </p>
        </div>
        <button className="secondary" onClick={onBack}>← Back to Home</button>
      </header>

      <MetricsCards summary={summary} />
      
      <section className="card margin-info">
        <h2>🚀 Arc Intelligence Layer</h2>
        <p>
          Aurelius coordinates specialized agents to validate, route, and execute AI tasks. 
          Every step is verified and settled using gasless USDC nanopayments via Circle & Arc.
        </p>
      </section>

      <div style={{ display: 'flex', gap: '20px', alignItems: 'center', marginBottom: '24px' }}>
        <PromptForm 
          onRun={handleRun} 
          onRouterRun={handleRouterRun}
          onBatchRun={handleBatchRun} 
          loading={loading} 
        />
        <div className="card simulation-control" style={{ margin: 0, flex: 1, textAlign: 'center' }}>
          <h3>🤖 Simulation Mode</h3>
          <p style={{ fontSize: '0.8rem', opacity: 0.7, marginBottom: '12px' }}>
            Automate autonomous agent commerce cycles using Featherless.
          </p>
          <button 
            className={isSimulating ? "danger" : "success"}
            onClick={() => setIsSimulating(!isSimulating)}
          >
            {isSimulating ? "Stop Simulation" : "Start Simulation"}
          </button>
        </div>
      </div>

      <div className="grid-two">
        <div className="content-panel">
          {run && <ValidatorPanel run={run} />}
          {routerResult && (
            <div className="card fade-in">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <h2>🔀 Global Router Output</h2>
                <span className="status-badge settled">Settled: ${routerResult.price_usdc} USDC</span>
              </div>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '16px' }}>
                <strong>Model:</strong> {routerResult.model_id}
              </p>
              <div style={{ background: 'rgba(0,0,0,0.2)', padding: '20px', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.05)', marginBottom: '16px' }}>
                 {routerResult.output}
              </div>
              <p style={{ fontSize: '0.85rem', fontStyle: 'italic', color: 'var(--text-muted)' }}>
                <strong>Reasoning:</strong> {routerResult.reasoning}
              </p>
            </div>
          )}
          {!run && !routerResult && (
            <div className="card" style={{ textAlign: 'center', padding: '60px', opacity: 0.5 }}>
              <p>Execute an agent to see the verification and settlement sequence.</p>
            </div>
          )}
        </div>
        <TransactionFeed summary={summary} isLive={isSimulating} />
      </div>
    </div>
  );
}
