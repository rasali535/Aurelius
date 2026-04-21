import { useEffect, useState } from "react";
import MetricsCards from "../components/MetricsCards";
import ValidatorPanel from "../components/ValidatorPanel";
import TransactionFeed from "../components/TransactionFeed";
import AgentNetworkGraphic from "../components/AgentNetworkGraphic";
import MarketTicker from "../components/MarketTicker";
import AgentPaymentFlow from "../components/AgentPaymentFlow";
import { api } from "../services/api";
import type { DashboardSummary, PromptRunResponse } from "../types";

export default function Dashboard({ onBack }: { onBack: () => void }) {
  const [run, setRun] = useState<PromptRunResponse | null>(null);
  const [routerResult, setRouterResult] = useState<any | null>(null);
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [isSimulating, setIsSimulating] = useState(true); // Default to automatic

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

  const handleRouterRun = async (task: string) => {
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
    }
  };

  return (
    <div className="page fade-in cyber-dashboard">
      <div className="glowing-blob blob-1"></div>
      <div className="glowing-blob blob-2"></div>
      
      <header className="cyber-header">
        <div className="system-status">
          <div className="status-bit">SYSTEM: <span style={{ color: 'var(--success)' }}>ONLINE</span></div>
          <div className="status-bit">NETWORK: <span style={{ color: 'var(--primary)' }}>ARC_TESTNET</span></div>
          <div className="status-bit">AUTO-PILOT: <span style={{ color: 'var(--secondary)' }}>{isSimulating ? 'ENABLED' : 'DISABLED'}</span></div>
        </div>
        <div className="system-identity">
          <h1>AURELIUS_CORE_v1.0</h1>
        </div>
        <button className="secondary" onClick={onBack} style={{ fontSize: '0.8rem', padding: '8px 16px' }}>TERMINATE_SESSION</button>
      </header>

      <div className="dashboard-grid-cyber">
        {/* Left Column: Diagnostics */}
        <div className="sidebar-diagnostics">
          <MetricsCards summary={summary} />

          <MarketTicker />
          
          <div className="card simulation-control">
            <h3 style={{ fontSize: '0.9rem', letterSpacing: '0.1em', color: 'var(--primary)', marginBottom: '12px' }}>AUTO_PILOT_ENGINE</h3>
            <p style={{ fontSize: '0.75rem', opacity: 0.6, marginBottom: '20px' }}>Automating agent commerce cycles via Featherless.</p>
            <button 
              className={isSimulating ? "danger" : "success"}
              onClick={() => setIsSimulating(!isSimulating)}
              style={{ width: '100%', fontSize: '0.8rem' }}
            >
              {isSimulating ? "SHUTDOWN_ENGINE" : "INIT_ENGINE"}
            </button>
          </div>
        </div>

        {/* Center Column: Neural Core */}
        <div className="neural-core">
          {/* Agent-to-Agent Payment Graph — always visible */}
          <AgentPaymentFlow isLive={isSimulating} />

          {/* Router/Validator output when a task fires */}
          {(run || routerResult) && (
            <ValidatorPanel 
              run={run}
              routerResult={routerResult}
            />
          )}

          <div className="global-pulse-container" style={{ marginTop: '40px', opacity: 0.25 }}>
             <AgentNetworkGraphic />
          </div>
        </div>

        {/* Right Column: Transaction Log */}
        <div className="transaction-log-column">
          <TransactionFeed summary={summary} isLive={isSimulating} />
        </div>
      </div>
    </div>
  );
}
