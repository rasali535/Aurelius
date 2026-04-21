import { useState } from "react";
import { api } from "../services/api";

export default function ManualPaymentPanel() {
  const [walletId, setWalletId] = useState("");
  const [amount, setAmount] = useState("0.01");
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<{ type: "success" | "error" | "none", msg: string }>({ type: "none", msg: "" });

  const handleManualPayment = async () => {
    if (!walletId) {
      setStatus({ type: "error", msg: "ERR: DEST_WALLET_ID_REQUIRED" });
      return;
    }

    setLoading(true);
    setStatus({ type: "none", msg: "INITIATING_BLOCKCHAIN_SETTLEMENT..." });
    
    try {
      const res = await api.post("/commerce/manual-payment", {
        destination_wallet_id: walletId,
        amount: parseFloat(amount),
      });
      
      setStatus({ 
        type: "success", 
        msg: `SUCCESS: TX_SIG: ${res.data.tx_hash.substring(0, 12)}...` 
      });
      setWalletId("");
    } catch (err: any) {
      setStatus({ 
        type: "error", 
        msg: `FAILED: ${err.response?.data?.detail || "SETTLEMENT_REJECTED"}` 
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card manual-payment-panel">
      <div className="panel-header">
        <h3 style={{ fontSize: '0.86rem', color: 'var(--secondary)', letterSpacing: '0.05em' }}>
          MANUAL_ON_CHAIN_SETTLEMENT
        </h3>
        <div className="protocol-badge">PROTOCOL: x402_DIRECT</div>
      </div>

      <div className="input-group">
        <label>DESTINATION_WALLET_ID</label>
        <input 
          type="text" 
          value={walletId}
          onChange={(e) => setWalletId(e.target.value)}
          placeholder="e.g. 0x..."
          className="cyber-input"
        />
      </div>

      <div className="input-group">
        <label>AMOUNT_USDC</label>
        <input 
          type="number" 
          value={amount}
          onChange={(e) => setAmount(e.target.value)}
          step="0.0001"
          className="cyber-input"
        />
      </div>

      <button 
        className="cyber-btn primary" 
        onClick={handleManualPayment}
        disabled={loading}
        style={{ marginTop: '10px', width: '100%' }}
      >
        {loading ? "PROCESSING..." : "EXECUTE_PAYMENT"}
      </button>

      {status.type !== "none" && (
        <div className={`status-box ${status.type}`}>
          {status.msg}
        </div>
      )}

      <style>{`
        .manual-payment-panel {
          border: 1px solid var(--secondary-low) !important;
          background: rgba(15, 10, 20, 0.6) !important;
        }
        .panel-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 15px;
        }
        .protocol-badge {
          font-size: 0.6rem;
          color: var(--primary);
          opacity: 0.7;
          font-family: var(--terminal-font);
        }
        .input-group {
          margin-bottom: 12px;
          display: flex;
          flex-direction: column;
          gap: 5px;
        }
        .input-group label {
          font-size: 0.65rem;
          color: var(--secondary);
          font-family: var(--terminal-font);
          letter-spacing: 0.05em;
        }
        .cyber-input {
          background: rgba(0, 0, 0, 0.4);
          border: 1px solid rgba(255, 255, 255, 0.1);
          color: white;
          padding: 8px;
          font-family: var(--terminal-font);
          font-size: 0.75rem;
          outline: none;
        }
        .cyber-input:focus {
          border-color: var(--secondary);
        }
        .status-box {
          margin-top: 15px;
          padding: 8px;
          font-size: 0.65rem;
          font-family: var(--terminal-font);
          border: 1px solid transparent;
        }
        .status-box.success {
          background: rgba(0, 255, 128, 0.1);
          color: var(--success);
          border-color: var(--success-low);
        }
        .status-box.error {
          background: rgba(255, 0, 85, 0.1);
          color: var(--error);
          border-color: var(--error-low);
        }
      `}</style>
    </div>
  );
}
