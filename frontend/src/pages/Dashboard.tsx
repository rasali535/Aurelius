import { useEffect, useState } from "react";
import MetricsCards from "../components/MetricsCards";
import ValidatorPanel from "../components/ValidatorPanel";
import TransactionFeed from "../components/TransactionFeed";
import AgentNetworkGraphic from "../components/AgentNetworkGraphic";
import MarketTicker from "../components/MarketTicker";
import AgentPaymentFlow from "../components/AgentPaymentFlow";
import SwapPanel from "../components/SwapPanel";
import { api } from "../services/api";
import type { DashboardSummary, PromptRunResponse } from "../types";

export default function Dashboard({ onBack }: { onBack: () => void }) {
  const [run, setRun] = useState<PromptRunResponse | null>(null);
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [isSimulating, setIsSimulating] = useState(true); 
  const [isBatchRunning, setIsBatchRunning] = useState(false);
  const [batchProgress, setBatchProgress] = useState(0);


  const fetchSummary = async () => {
    try {
      const res = await api.get("/dashboard/summary");
      if (res.data && res.data.total_prompt_runs !== undefined) {
        setSummary(res.data);
      }
    } catch (err) {
      console.error("Critical: Summary data fetch failed", err);
    }
  };

  useEffect(() => {
    fetchSummary();
    const interval = setInterval(fetchSummary, 10000); 
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    let simInterval: any;
    if (isSimulating && !isBatchRunning) {
      simInterval = setInterval(async () => {
        const tasks = [
          "Validate smart contract security",
          "Check PII in user data",
          "Analyze cross-chain arbitrage",
          "Verify identity of agent V-9",
          "Route transaction to optimal liquidity"
        ];
        const randomTask = tasks[Math.floor(Math.random() * tasks.length)];
        handleRouterRun(randomTask);
      }, 10000);
    }
    return () => clearInterval(simInterval);
  }, [isSimulating, isBatchRunning]);

  const handleRouterRun = async (task: string) => {
    try {
      await api.post("/router/execute", { task });
      await fetchSummary();
    } catch (err) {
      console.error("Router execution failed", err);
    }
  };

  const startBatchDemo = async () => {
    setIsBatchRunning(true);
    setBatchProgress(0);
    
    // Start the heavy batch on the backend
    api.post("/run-demo-batch").catch(e => console.error("Batch failed", e));
    
    // Simulate UI progress while polling summary
    const duration = 15000; // 15s for the batch
    const interval = 100;
    const steps = duration / interval;
    let currentStep = 0;
    
    const progressInterval = setInterval(() => {
      currentStep++;
      const progress = Math.min((currentStep / steps) * 100, 99);
      setBatchProgress(progress);
      
      if (currentStep >= steps) {
        clearInterval(progressInterval);
        setBatchProgress(100);
        setTimeout(() => {
            setIsBatchRunning(false);
            fetchSummary();
        }, 1000);
      }
    }, interval);
  };

  return (
    <div className="page fade-in cyber-dashboard">
      <div className="glowing-blob blob-1"></div>
      <div className="glowing-blob blob-2"></div>
      
      <header className="cyber-header">
        <div className="system-status">
          <div className="status-bit">SYSTEM: <span style={{ color: 'var(--success)' }}>ONLINE</span></div>
          <div className="status-bit">NETWORK: <span style={{ color: 'var(--primary)' }}>ARC_TESTNET</span></div>
          <div className="status-bit">WALLET_ID: <span style={{ color: 'var(--secondary)' }}>{summary?.wallet_id || 'PENDING...'}</span></div>
          <div className="status-bit">ADDRESS: <span style={{ color: 'var(--primary)', fontSize: '0.7rem' }}>{summary?.wallet_address || '0x...'}</span></div>
        </div>
        <div className="system-identity">
          <h1>AURELIUS_CORE_v1.0</h1>
        </div>
        <button className="secondary" onClick={onBack} style={{ fontSize: '0.8rem', padding: '8px 16px' }}>TERMINATE_SESSION</button>
      </header>

      <div className="cyber-frame">
        <div className="dashboard-grid-cyber">
        {/* Left Column: Diagnostics */}
        <div className="sidebar-diagnostics">
          <MetricsCards summary={summary} />

          {/* Batch Demo Trigger */}
          <div className="card batch-demo-panel">
            <h3 style={{ fontSize: '0.86rem', color: 'var(--primary)', marginBottom: 8, letterSpacing: '0.05em' }}>HACKATHON_DEMO_SEQUENCE</h3>
            <p style={{ fontSize: '0.7rem', opacity: 0.6, marginBottom: 15 }}>Execute 60+ on-chain settlements (12 runs × 5 nodes).</p>
            
            {isBatchRunning ? (
                <div className="progress-section">
                    <div className="progress-container">
                        <div className="progress-bar" style={{ width: `${batchProgress}%` }}></div>
                    </div>
                    <div className="batch-status">
                         <span className="blink">EXECUTING_SETTLEMENTS...</span>
                         <span>{Math.round(batchProgress)}%</span>
                    </div>
                </div>
            ) : (
                <button 
                  className="cyber-btn" 
                  onClick={startBatchDemo}
                  style={{ width: '100%', fontSize: '0.75rem', padding: '10px' }}
                >
                  START_BATCH_DEMO
                </button>
            )}
          </div>

          <MarketTicker />

          <SwapPanel summary={summary} />
          
          <div className="card simulation-control">
            <h3 style={{ fontSize: '0.86rem', color: 'var(--success)', marginBottom: '8px' }}>AUTO_PILOT_ENGINE</h3>
            <p style={{ fontSize: '0.7rem', opacity: 0.6, marginBottom: '15px' }}>Cyclic agent commerce via Featherless API.</p>
            <button 
              className={isSimulating ? "danger" : "success"}
              onClick={() => setIsSimulating(!isSimulating)}
              style={{ width: '100%', fontSize: '0.75rem', padding: '10px' }}
              disabled={isBatchRunning}
            >
              {isSimulating ? "SHUTDOWN_ENGINE" : "INIT_ENGINE"}
            </button>
          </div>
        </div>

        {/* Center Column: Neural Core */}
        <div className="neural-core">
          <AgentPaymentFlow isLive={isSimulating || isBatchRunning} />

          {run && (
            <ValidatorPanel 
              run={run}
            />
          )}

          <div className="global-pulse-container" style={{ marginTop: '40px', opacity: 0.15 }}>
             <AgentNetworkGraphic />
          </div>
        </div>

        {/* Right Column: Transaction Log */}
        <div className="transaction-log-column">
          <TransactionFeed summary={summary} isLive={isSimulating || isBatchRunning} />
        </div>
        </div>
      </div>
    </div>
  );
}
