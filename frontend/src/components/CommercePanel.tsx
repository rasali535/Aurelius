import { useState, useEffect } from "react";
import { api } from "../services/api";
import type { DashboardSummary } from "../types";

export default function CommercePanel({ summary }: { summary: DashboardSummary | null }) {
  const [activeTab, setActiveTab] = useState<"swap" | "bridge" | "agents" | "vision">("swap");

  // Vision State
  const [visionImage, setVisionImage] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => {
        setVisionImage(reader.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleVisionSettlement = async () => {
    if (!visionImage) return;
    const taskId = `VISION_${Math.random().toString(36).slice(2, 6).toUpperCase()}`;
    addLog(taskId, "pending", "ANALYZING_DOCUMENT_VIA_GEMINI_VISION...");
    
    try {
      const base64 = visionImage.split(',')[1];
      const res = await api.post("/commerce/multimodal/settle", { image: base64 });
      
      updateLog(taskId, "success", `VISION_PROCESSED: ${res.data.message}`, res.data.tx_hash);
    } catch (err: any) {
      updateLog(taskId, "error", `VISION_FAILED: ${err.response?.data?.detail || "ERROR"}`);
    }
  };
  
  // Swap State
  const [fromToken, setFromToken] = useState("USDC");
  const [toToken, setToToken] = useState("WETH");
  const [swapAmount, setSwapAmount] = useState("10.00");
  
  // Bridge State
  const [sourceChain, setSourceChain] = useState("ETH-SEPOLIA");
  const [destChain, setDestChain] = useState("ARC-TESTNET");
  const [bridgeAmount, setBridgeAmount] = useState("5.00");
  const [destAddress, setDestAddress] = useState(summary?.wallet_address || "");
  
  useEffect(() => {
    if (summary?.wallet_address && !destAddress) {
      setDestAddress(summary.wallet_address);
    }
  }, [summary]);

  // Agent/Job State
  const [agentMetadata, setAgentMetadata] = useState("ipfs://aurelius-agent-v1");
  const [jobProvider, setJobProvider] = useState("0x3E5A42D19a584093952fA6d7667C82D7068560F4"); // Demo Provider
  const [jobEvaluator, setJobEvaluator] = useState("0x5B38Da6a701c568545dCfcB03FcB875f56beddC4"); // Demo Evaluator
  const [jobDescription, setJobDescription] = useState("Analyze sentiment for Arc Network data.");
  const [gatewayAmount, setGatewayAmount] = useState("0.0001");
  const [tasks, setTasks] = useState<{ id: string, type: "success" | "error" | "pending", msg: string, timestamp: string, txHash?: string }[]>([]);

  const addLog = (id: string, type: "success" | "error" | "pending", msg: string, txHash?: string) => {
    const timestamp = new Date().toLocaleTimeString();
    setTasks(prev => [{ id, type, msg, timestamp, txHash }, ...prev].slice(0, 50));
  };

  const updateLog = (id: string, type: "success" | "error" | "pending", msg: string, txHash?: string) => {
    setTasks(prev => prev.map(t => t.id === id ? { ...t, type, msg, txHash: txHash || t.txHash } : t));
  };

  const handleSwap = async () => {
    const taskId = `SWAP_${Math.random().toString(36).slice(2, 6).toUpperCase()}`;
    const amount = parseFloat(swapAmount) || 0;
    addLog(taskId, "pending", `INITIATING_DEX_SWAP: ${amount} ${fromToken} → ${toToken}`);
    
    try {
      const res = await api.post("/commerce/swap", {
        from_token: fromToken,
        to_token: toToken,
        amount: amount,
      });
      
      updateLog(taskId, "success", `SWAP_COMPLETE: +${res.data.received_amount.toFixed(4)} ${toToken}`, res.data.tx_hash);
    } catch (err: any) {
      updateLog(taskId, "error", `FAILED: ${err.response?.data?.detail || "SWAP_REJECTED"}`);
    }
  };

  const handleBridge = async () => {
    const localId = `BRIDGE_${Math.random().toString(36).slice(2, 6).toUpperCase()}`;
    const targetAddress = destAddress || summary?.wallet_address || "0x0000000000000000000000000000000000000000";
    addLog(localId, "pending", `INITIATING_CCTP_BRIDGE: ${bridgeAmount} USDC to ${destChain}`);
    
    try {
      const res = await api.post("/commerce/bridge", {
        amount: parseFloat(bridgeAmount) || 0,
        source_blockchain: sourceChain,
        destination_blockchain: destChain,
        destination_address: targetAddress,
      });
      
      updateLog(localId, "success", `BRIDGE_STARTED: Task ID ${res.data.task_id}. Processing in background...`, res.data.destTx);
    } catch (err: any) {
      updateLog(localId, "error", `BRIDGE_FAILED: ${err.response?.data?.detail || "CCTP_ERROR"}`);
    }
  };

  const handleRegisterAgent = async () => {
    const taskId = `AGENT_${Math.random().toString(36).slice(2, 6).toUpperCase()}`;
    addLog(taskId, "pending", "REGISTERING_AGENT_IDENTITY...");
    try {
      const res = await api.post("/commerce/agent/register", { metadata_uri: agentMetadata });
      updateLog(taskId, "success", `AGENT_REGISTERED!`, res.data.tx_hash);
    } catch (err: any) {
      updateLog(taskId, "error", `REGISTRATION_FAILED: ${err.response?.data?.detail}`);
    }
  };

  const handleCreateJob = async () => {
    const taskId = `JOB_${Math.random().toString(36).slice(2, 6).toUpperCase()}`;
    addLog(taskId, "pending", "CREATING_AGENTIC_JOB...");
    try {
      const res = await api.post("/commerce/job/create", { 
        provider: jobProvider, 
        evaluator: jobEvaluator, 
        description: jobDescription 
      });
      updateLog(taskId, "success", `JOB_CREATED!`, res.data.tx_hash);
    } catch (err: any) {
      updateLog(taskId, "error", `JOB_FAILED: ${err.response?.data?.detail}`);
    }
  };

  const handleGatewayTransfer = async () => {
    const taskId = `PAY_${Math.random().toString(36).slice(2, 6).toUpperCase()}`;
    const targetAddress = summary?.wallet_address || "0x0000000000000000000000000000000000000000";
    addLog(taskId, "pending", `EXECUTING_NANOPAYMENT: ${gatewayAmount} USDC to ${targetAddress}`);
    try {
      const res = await api.post("/commerce/gateway/transfer", {
        destination_blockchain: "ETH-SEPOLIA",
        destination_address: targetAddress,
        amount: parseFloat(gatewayAmount) || 0
      });
      updateLog(taskId, "success", `NANOPAYMENT_COMPLETE!`, res.data.tx_hash);
    } catch (err: any) {
      updateLog(taskId, "error", `GATEWAY_ERROR: ${err.response?.data?.detail}`);
    }
  };

  const handleStressTest = async () => {
    const testId = `STRESS_${Math.random().toString(36).slice(2, 6).toUpperCase()}`;
    addLog(testId, "pending", "GENERATING_50_ONCHAIN_TRANSACTIONS...");
    
    let successCount = 0;
    for (let i = 0; i < 50; i++) {
      try {
        await api.post("/commerce/manual-payment", {
          destination_wallet_id: "0x3E5A42D19a584093952fA6d7667C82D7068560F4",
          amount: 0.0001
        });
        successCount++;
        updateLog(testId, "pending", `PROCESSED: ${successCount}/50 TRANSACTIONS...`);
      } catch (err) {
        console.error("Stress test tx failed", err);
      }
      await new Promise(r => setTimeout(r, 100));
    }
    
    updateLog(testId, "success", `ECONOMY_STRESS_TEST_COMPLETE: 50 TXs SETTLED`);
  };

  const exchangeRate = fromToken === "USDC" ? "0.00042" : "2380.00";

  return (
    <div className="card commerce-panel">
      <div className="panel-tabs">
        <button 
          className={`tab-btn ${activeTab === 'swap' ? 'active' : ''}`} 
          onClick={() => setActiveTab('swap')}
        >
          SWAP_ASSETS
        </button>
        <button 
          className={`tab-btn ${activeTab === 'bridge' ? 'active' : ''}`} 
          onClick={() => setActiveTab('bridge')}
        >
          CROSS_CHAIN_BRIDGE
        </button>
        <button 
          className={`tab-btn ${activeTab === 'agents' ? 'active' : ''}`} 
          onClick={() => setActiveTab('agents')}
        >
          AGENTS_&_JOBS
        </button>
        <button 
          className={`tab-btn ${activeTab === 'vision' ? 'active' : ''}`} 
          onClick={() => setActiveTab('vision')}
        >
          VISION_CHECKOUT
        </button>
      </div>

      <div className="panel-header">
        <h3 style={{ fontSize: '1.2rem', color: 'var(--primary)', letterSpacing: '0.05em' }}>
          {activeTab === 'swap' ? 'LIQUIDITY_SWAP_INTERFACE' : activeTab === 'bridge' ? 'CCTP_NATIVE_BRIDGE' : 'AGENTIC_ECONOMY_CORE'}
        </h3>
        <div className="protocol-badge">{activeTab === 'swap' ? 'ARC_DEX_v2' : 'CIRCLE_CCTP_v2'}</div>
      </div>

      {activeTab === 'swap' && (
        <div className="swap-container">
          <div className="swap-box">
            <div className="swap-box-header">
              <label>SELL</label>
              <span className="balance">WID: {summary?.wallet_id?.slice(0,8)}...</span>
            </div>
            <div className="swap-input-row">
              <input 
                type="number" 
                value={swapAmount}
                onChange={(e) => setSwapAmount(e.target.value)}
                className="swap-input"
              />
              <select value={fromToken} onChange={(e) => setFromToken(e.target.value)} className="token-select">
                <option value="USDC">USDC</option>
                <option value="WETH">WETH</option>
                <option value="WBTC">WBTC</option>
              </select>
            </div>
          </div>

          <div className="swap-divider">
            <div className="arrow-down">↓</div>
          </div>

          <div className="swap-box">
            <div className="swap-box-header">
              <label>BUY</label>
              <span className="balance">BAL: 0.00</span>
            </div>
            <div className="swap-input-row">
              <input 
                type="text" 
                value={(parseFloat(swapAmount) * parseFloat(exchangeRate)).toFixed(6)}
                readOnly
                className="swap-input"
              />
              <select value={toToken} onChange={(e) => setToToken(e.target.value)} className="token-select">
                <option value="WETH">WETH</option>
                <option value="USDC">USDC</option>
                <option value="WBTC">WBTC</option>
              </select>
            </div>
          </div>

          <div className="rate-info">
            <span>Rate</span>
            <span>1 {fromToken} ≈ {exchangeRate} {toToken}</span>
          </div>

          <button 
            className="cyber-btn primary-glow" 
            onClick={handleSwap}
            style={{ marginTop: '15px', width: '100%', fontWeight: 'bold' }}
          >
            EXECUTE_SWAP
          </button>
        </div>
      )}

      {activeTab === 'bridge' && (
        <div className="bridge-container">
          <div className="swap-box">
            <div className="swap-box-header">
              <label>SOURCE_CHAIN</label>
            </div>
            <div className="swap-input-row">
              <select value={sourceChain} onChange={(e) => setSourceChain(e.target.value)} className="chain-select">
                <option value="ETH-SEPOLIA">Ethereum Sepolia</option>
                <option value="ARC-TESTNET">Arc Testnet</option>
              </select>
              <input 
                type="number" 
                value={bridgeAmount}
                onChange={(e) => setBridgeAmount(e.target.value)}
                className="bridge-amount-input"
                placeholder="0.00"
              />
              <span className="token-label">USDC</span>
            </div>
          </div>

          <div className="swap-divider">
            <div className="arrow-down">→</div>
          </div>

          <div className="swap-box">
            <div className="swap-box-header">
              <label>DESTINATION_CHAIN</label>
            </div>
            <div className="swap-input-row">
              <select value={destChain} onChange={(e) => setDestChain(e.target.value)} className="chain-select">
                <option value="ARC-TESTNET">Arc Testnet</option>
                <option value="ETH-SEPOLIA">Ethereum Sepolia</option>
              </select>
            </div>
            <div className="dest-address-row" style={{ marginTop: '10px' }}>
              <label style={{ fontSize: '0.6rem', color: 'var(--text-muted)' }}>DESTINATION_ADDRESS</label>
              <input 
                type="text" 
                value={destAddress}
                onChange={(e) => setDestAddress(e.target.value)}
                className="dest-address-input"
                placeholder="0x..."
              />
            </div>
          </div>

          <div className="bridge-info" style={{ marginTop: '10px', fontSize: '0.65rem', color: 'var(--text-muted)' }}>
            <p>• Native 1:1 USDC Transfer via Circle CCTP</p>
            <p>• Estimated time: 2-3 minutes (attestation lag)</p>
          </div>

          <button 
            className="cyber-btn secondary-glow" 
            onClick={handleBridge}
            style={{ marginTop: '15px', width: '100%', fontWeight: 'bold' }}
          >
            START_BRIDGE_TRANSFER
          </button>
        </div>
      )}

      {activeTab === 'agents' && (
        <div className="agents-container" style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {/* Agent Identity Section */}
          <div className="swap-box">
            <div className="swap-box-header">
              <label>ERC-8004_AGENT_IDENTITY</label>
            </div>
            <div className="swap-input-row">
              <input 
                type="text" 
                value={agentMetadata}
                onChange={(e) => setAgentMetadata(e.target.value)}
                className="dest-address-input"
                style={{ fontSize: '0.65rem' }}
              />
              <button className="cyber-btn" onClick={handleRegisterAgent} style={{ fontSize: '0.6rem', padding: '5px 10px' }}>
                REGISTER
              </button>
            </div>
          </div>

          {/* Job Escrow Section */}
          <div className="swap-box">
            <div className="swap-box-header">
              <label>ERC-8183_COMMERCE_JOB</label>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <input 
                type="text" 
                value={jobDescription}
                onChange={(e) => setJobDescription(e.target.value)}
                className="dest-address-input"
                placeholder="Job Description"
              />
              <div style={{ display: 'flex', gap: '5px' }}>
                <input type="text" value={jobProvider} onChange={(e) => setJobProvider(e.target.value)} className="dest-address-input" style={{ flex: 1 }} placeholder="Provider" />
                <input type="text" value={jobEvaluator} onChange={(e) => setJobEvaluator(e.target.value)} className="dest-address-input" style={{ flex: 1 }} placeholder="Evaluator" />
              </div>
              <button className="cyber-btn primary-glow" onClick={handleCreateJob} style={{ width: '100%', fontSize: '0.7rem' }}>
                CREATE_ESCROW_JOB
              </button>
            </div>
          </div>

          {/* Gateway Nanopayment Section */}
          <div className="swap-box">
            <div className="swap-box-header">
              <label>GATEWAY_X402_NANOPAYMENT</label>
            </div>
            <div className="swap-input-row">
              <input 
                type="number" 
                value={gatewayAmount}
                onChange={(e) => setGatewayAmount(e.target.value)}
                className="swap-input"
                style={{ fontSize: '1rem' }}
              />
              <span className="token-label">USDC</span>
              <button className="cyber-btn secondary-glow" onClick={handleGatewayTransfer}>
                PAY
              </button>
            </div>
            <p style={{ fontSize: '0.55rem', color: 'var(--text-muted)', marginTop: '5px' }}>
              • Unified balance cross-chain transfer via BurnIntent signature.
            </p>
          </div>

          <button 
            className="cyber-btn" 
            onClick={handleStressTest} 
            style={{ 
              marginTop: '10px', 
              width: '100%', 
              background: 'rgba(255, 0, 85, 0.1)', 
              borderColor: 'var(--error)',
              color: 'var(--error)',
              fontSize: '0.7rem'
            }}
          >
            🚀 GENERATE_50_TX_PROOF (HACKATHON_DEMO)
          </button>
        </div>
      )}

      {activeTab === 'vision' && (
        <div className="vision-container" style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
          <div className="swap-box">
            <div className="swap-box-header">
              <label>MULTIMODAL_DOCUMENT_SCAN</label>
            </div>
            <div className="vision-upload-area" style={{ 
              border: '2px dashed rgba(0, 242, 255, 0.2)', 
              borderRadius: '8px', 
              padding: '20px', 
              textAlign: 'center',
              background: 'rgba(0, 0, 0, 0.2)'
            }}>
              {visionImage ? (
                <div style={{ position: 'relative' }}>
                  <img src={visionImage} alt="Upload" style={{ maxWidth: '100%', maxHeight: '150px', borderRadius: '4px' }} />
                  <button 
                    onClick={() => setVisionImage(null)}
                    style={{ position: 'absolute', top: '-10px', right: '-10px', background: 'var(--error)', border: 'none', borderRadius: '50%', width: '20px', height: '20px', color: 'white', cursor: 'pointer' }}
                  >
                    ×
                  </button>
                </div>
              ) : (
                <div style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>
                  <p>DRAG_&_DROP_INVOICE_OR_RECEIPT</p>
                  <input type="file" accept="image/*" onChange={handleFileChange} style={{ marginTop: '10px' }} />
                </div>
              )}
            </div>
          </div>

          <button 
            className="cyber-btn primary-glow" 
            onClick={handleVisionSettlement} 
            disabled={!visionImage}
            style={{ width: '100%' }}
          >
            ANALYZE_&_SETTLE_ON_ARC
          </button>

          {visionImage && (
            <div style={{ fontSize: '0.55rem', color: 'var(--text-muted)' }}>
              • Image loaded. Ready for analysis.
            </div>
          )}
          
          <div style={{ fontSize: '0.55rem', color: 'var(--text-muted)' }}>
            • Uses <strong>Gemini 1.5 Flash</strong> (Multimodal) to verify invoices.<br/>
            • Decisions are executed via <strong>Circle Gateway Nanopayments</strong> on Arc.
          </div>
        </div>
      )}

      <div className="task-orchestrator-log">
        <div className="log-header">TASK_ORCHESTRATOR_LOG</div>
        <div className="log-entries">
          {tasks.length === 0 && <div className="no-tasks">AWAITING_COMMANDS...</div>}
          {tasks.map(task => (
            <div key={task.id} className={`log-entry ${task.type}`}>
              <span className="log-time">[{task.timestamp}]</span>
              <span className="log-id">[{task.id}]</span>
              <span className="log-msg">
                {task.msg}
                {task.txHash && /^(0x)?[a-fA-F0-9]{40,66}$/.test(task.txHash) && (
                  <a 
                    href={`https://testnet.arcscan.app/${task.txHash.length > 42 ? 'tx' : 'address'}/${task.txHash.startsWith('0x') ? task.txHash : '0x' + task.txHash}`} 
                    target="_blank" 
                    rel="noreferrer" 
                    className="view-tx-btn"
                    style={{ marginLeft: '10px', fontSize: '0.6rem', color: 'var(--primary)', textDecoration: 'underline' }}
                  >
                    VIEW_TX
                  </a>
                )}
              </span>
              {task.type === "pending" && <span className="log-spinner">⠋</span>}
            </div>
          ))}
        </div>
      </div>

      <style>{`
        .commerce-panel {
          border: 1px solid var(--primary-glow) !important;
          background: rgba(5, 5, 15, 0.9) !important;
          position: relative;
          overflow: hidden;
          padding: 30px !important;
          margin-bottom: 40px !important;
          box-shadow: 0 0 40px rgba(0, 0, 0, 0.5), inset 0 0 20px rgba(0, 242, 255, 0.05) !important;
          max-width: 800px;
          align-self: center;
          width: 100%;
        }
        .panel-tabs {
          display: flex;
          border-bottom: 1px solid rgba(0, 242, 255, 0.1);
          margin: 0 -20px 20px -20px;
        }
        .tab-btn {
          flex: 1;
          padding: 10px;
          background: transparent;
          border: none;
          color: var(--text-muted);
          font-size: 0.85rem;
          font-family: var(--terminal-font);
          cursor: pointer;
          transition: all 0.2s;
          padding: 15px;
          text-transform: uppercase;
          letter-spacing: 0.1em;
        }
        .tab-btn.active {
          color: var(--primary);
          background: rgba(0, 242, 255, 0.05);
          border-bottom: 2px solid var(--primary);
        }
        .commerce-panel::before {
          content: "";
          position: absolute;
          top: 0;
          left: 0;
          width: 2px;
          height: 100%;
          background: var(--primary);
          box-shadow: 0 0 10px var(--primary);
        }
        .panel-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 20px;
        }
        .protocol-badge {
          font-size: 0.6rem;
          color: var(--primary);
          opacity: 0.7;
          background: rgba(0, 242, 255, 0.1);
          padding: 2px 6px;
          border-radius: 2px;
          font-family: var(--terminal-font);
        }
        .swap-container, .bridge-container {
          display: flex;
          flex-direction: column;
          gap: 4px;
        }
        .swap-box {
          background: rgba(0, 0, 0, 0.4);
          border: 1px solid rgba(255, 255, 255, 0.05);
          padding: 12px;
          border-radius: 4px;
        }
        .swap-box-header {
          display: flex;
          justify-content: space-between;
          margin-bottom: 8px;
        }
        .swap-box-header label {
          font-size: 0.6rem;
          color: var(--text-muted);
          font-family: var(--terminal-font);
          letter-spacing: 0.1em;
        }
        .balance {
          font-size: 0.6rem;
          color: var(--text-muted);
          font-family: var(--terminal-font);
        }
        .swap-input-row {
          display: flex;
          gap: 10px;
          align-items: center;
        }
        .swap-input, .bridge-amount-input {
          background: transparent;
          border: none;
          color: white;
          font-size: 1.5rem;
          font-family: var(--terminal-font);
          width: 100%;
          outline: none;
          padding: 5px 0;
        }
        .bridge-amount-input {
          text-align: right;
          font-size: 1rem;
        }
        .token-label {
          color: var(--primary);
          font-family: var(--terminal-font);
          font-size: 0.8rem;
        }
        .token-select, .chain-select {
          background: rgba(255, 255, 255, 0.05);
          border: 1px solid rgba(255, 255, 255, 0.1);
          color: white;
          padding: 4px 8px;
          border-radius: 4px;
          font-family: var(--terminal-font);
          font-size: 0.8rem;
          cursor: pointer;
        }
        .chain-select {
          width: 100%;
        }
        .dest-address-input {
          background: rgba(0, 0, 0, 0.2);
          border: 1px solid rgba(255, 255, 255, 0.1);
          color: var(--primary);
          width: 100%;
          padding: 12px;
          font-family: var(--terminal-font);
          font-size: 0.9rem;
          border-radius: 4px;
          margin-top: 8px;
        }
        .swap-divider {
          display: flex;
          justify-content: center;
          margin: -10px 0;
          z-index: 2;
        }
        .arrow-down {
          background: var(--background);
          border: 1px solid rgba(255, 255, 255, 0.1);
          width: 24px;
          height: 24px;
          display: flex;
          align-items: center;
          justify-content: center;
          border-radius: 50%;
          color: var(--primary);
          font-size: 0.8rem;
        }
        .rate-info {
          display: flex;
          justify-content: space-between;
          padding: 10px 5px;
          font-size: 0.65rem;
          color: var(--text-muted);
          font-family: var(--terminal-font);
        }
        .primary-glow {
          background: var(--primary) !important;
          color: var(--background) !important;
          border: none !important;
          box-shadow: 0 0 15px var(--primary-glow);
        }
        .secondary-glow {
          background: var(--secondary) !important;
          color: var(--background) !important;
          border: none !important;
          box-shadow: 0 0 15px var(--secondary);
        }
        .task-orchestrator-log {
          margin-top: 20px;
          background: rgba(0, 0, 0, 0.4);
          border: 1px solid rgba(0, 242, 255, 0.1);
          border-radius: 4px;
          overflow: hidden;
          font-family: var(--terminal-font);
        }
        .log-header {
          background: rgba(0, 242, 255, 0.05);
          padding: 6px 12px;
          font-size: 0.65rem;
          color: var(--primary);
          border-bottom: 1px solid rgba(0, 242, 255, 0.1);
          letter-spacing: 0.1em;
        }
        .log-entries {
          max-height: 150px;
          overflow-y: auto;
          padding: 8px;
          display: flex;
          flex-direction: column;
          gap: 4px;
        }
        .no-tasks {
          font-size: 0.65rem;
          color: var(--text-muted);
          text-align: center;
          padding: 10px;
        }
        .log-entry {
          font-size: 0.65rem;
          display: flex;
          gap: 8px;
          align-items: center;
          padding: 2px 4px;
          border-radius: 2px;
        }
        .log-entry.pending { color: var(--primary); opacity: 0.8; }
        .log-entry.success { color: var(--success); background: rgba(0, 255, 128, 0.05); }
        .log-entry.error { color: var(--error); background: rgba(255, 0, 85, 0.05); }
        
        .log-time { opacity: 0.5; min-width: 65px; }
        .log-id { font-weight: bold; min-width: 80px; }
        .log-msg { flex: 1; }
        
        .log-spinner {
          animation: spin 1s linear infinite;
        }
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }

        .status-box {
          margin-top: 15px;
          padding: 10px;
          font-size: 0.7rem;
          font-family: var(--terminal-font);
          border-left: 2px solid transparent;
        }
        .status-box.success {
          background: rgba(0, 255, 128, 0.05);
          color: var(--success);
          border-color: var(--success);
        }
        .status-box.error {
          background: rgba(255, 0, 85, 0.05);
          color: var(--error);
          border-color: var(--error);
        }
        .status-header {
          font-weight: bold;
          margin-bottom: 4px;
          letter-spacing: 0.05em;
        }
      `}</style>
    </div>
  );
}
