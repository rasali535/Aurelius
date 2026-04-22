import { useState } from "react";
import { api } from "../services/api";
import type { DashboardSummary } from "../types";

export default function SwapPanel({ summary }: { summary: DashboardSummary | null }) {
  const [fromToken, setFromToken] = useState("USDC");
  const [toToken, setToToken] = useState("WETH");
  const [amount, setAmount] = useState("10.00");
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<{ type: "success" | "error" | "none", msg: string }>({ type: "none", msg: "" });

  const handleSwap = async () => {
    setLoading(true);
    setStatus({ type: "none", msg: "INITIATING_DEX_SWAP..." });
    
    try {
      const res = await api.post("/commerce/swap", {
        from_token: fromToken,
        to_token: toToken,
        amount: parseFloat(amount),
        wallet_id: summary?.wallet_id,
      });
      
      setStatus({ 
        type: "success", 
        msg: `SWAP_COMPLETE: +${res.data.received_amount.toFixed(4)} ${toToken}` 
      });
    } catch (err: any) {
      setStatus({ 
        type: "error", 
        msg: `FAILED: ${err.response?.data?.detail || "SWAP_REJECTED"}` 
      });
    } finally {
      setLoading(false);
    }
  };

  const exchangeRate = fromToken === "USDC" ? "0.00042" : "2380.00";

  return (
    <div className="card swap-panel">
      <div className="panel-header">
        <h3 style={{ fontSize: '0.86rem', color: 'var(--primary)', letterSpacing: '0.05em' }}>
          LIQUIDITY_SWAP_INTERFACE
        </h3>
        <div className="protocol-badge">ARC_DEX_v2</div>
      </div>

      <div className="swap-container">
        <div className="swap-box">
          <div className="swap-box-header">
            <label>SELL</label>
            <span className="balance">WID: {summary?.wallet_id?.slice(0,8)}...</span>
          </div>
          <div className="swap-input-row">
            <input 
              type="number" 
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
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
              value={(parseFloat(amount) * parseFloat(exchangeRate)).toFixed(6)}
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
          disabled={loading}
          style={{ marginTop: '15px', width: '100%', fontWeight: 'bold' }}
        >
          {loading ? "ROUTING_TRANSACTION..." : "EXECUTE_SWAP"}
        </button>
      </div>

      <div style={{ minHeight: '60px', marginTop: '15px' }}>
        {status.type !== "none" && (
          <div className={`status-box ${status.type}`} style={{ margin: 0 }}>
            <div className="status-header">
              {status.type === "success" ? "✓ TRANSACTION_VERIFIED" : "⚠ SYSTEM_ERROR"}
            </div>
            <div className="status-msg">{status.msg}</div>
          </div>
        )}
      </div>

      <style>{`
        .swap-panel {
          border: 1px solid var(--primary-low) !important;
          background: rgba(5, 5, 15, 0.8) !important;
          position: relative;
          overflow: hidden;
        }
        .swap-panel::before {
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
        .swap-container {
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
        .swap-input {
          background: transparent;
          border: none;
          color: white;
          font-size: 1.2rem;
          font-family: var(--terminal-font);
          width: 100%;
          outline: none;
        }
        .token-select {
          background: rgba(255, 255, 255, 0.05);
          border: 1px solid rgba(255, 255, 255, 0.1);
          color: white;
          padding: 4px 8px;
          border-radius: 4px;
          font-family: var(--terminal-font);
          font-size: 0.8rem;
          cursor: pointer;
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
