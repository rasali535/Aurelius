import { useEffect, useState } from "react";
import type { DashboardSummary, Transaction } from "../types";

type Props = {
  summary: DashboardSummary | null;
  isLive?: boolean;
};

export default function TransactionFeed({ summary, isLive }: Props) {
  const [localTxs, setLocalTxs] = useState<Transaction[]>([]);

  useEffect(() => {
    if (summary?.latest_transactions) {
      setLocalTxs(summary.latest_transactions);
    }
  }, [summary]);

  // Simulation: Add random fake pending transactions when live to show network activity
  useEffect(() => {
    if (!isLive) return;
    const interval = setInterval(() => {
      const newTx: Transaction = {
        id: `TX_${Math.random().toString(36).substr(2, 6).toUpperCase()}`,
        amount_usdc: +(Math.random() * 0.01).toFixed(4),
        status: "settled",
        tx_hash: `0x${Math.random().toString(16).substr(2, 64)}`,
        settled_at: new Date().toISOString(),
        x402_status: Math.random() > 0.5 ? "paid" : "settled"
      };
      setLocalTxs(prev => [newTx, ...prev].slice(0, 20));
    }, 4500);
    return () => clearInterval(interval);
  }, [isLive]);

  return (
    <div className="card transaction-feed-card">
      <div className="ticker-header" style={{ marginBottom: 20 }}>
        <span style={{ fontFamily: "var(--terminal-font)", fontSize: "0.8rem", color: "var(--primary)", letterSpacing: "0.15em" }}>
          LIVE_SETTLEMENT_FEED
        </span>
        {isLive && (
          <div className="live-indicator">
            <span className="blink"></span>
            SYNCING
          </div>
        )}
      </div>

      <div className="transaction-list-cyber">
        {localTxs.length > 0 ? (
          localTxs.map((tx) => (
            <div key={tx.id || tx.tx_hash} className="tx-row-cyber new-tx-animate">
              <div className="tx-main">
                <div className="tx-id-row">
                  <span className="tx-id-token">{tx.id || "SETTLEMENT"}</span>
                  <span className={`tx-tag ${tx.x402_status === "paid" ? "tag-x402" : "tag-std"}`}>
                    {tx.x402_status === "paid" ? "X402_PROOF" : "BASE_AUTH"}
                  </span>
                </div>
                <div className="tx-hash-row">
                   <a 
                    href={`https://testnet.arcscan.app/tx/${tx.tx_hash}`} 
                    target="_blank" 
                    rel="noreferrer"
                    className="arc-link"
                  >
                    {tx.tx_hash ? `${tx.tx_hash.slice(0, 18)}...` : "PENDING_ON_CHAIN"}
                  </a>
                </div>
              </div>
              <div className="tx-amount-side">
                <div className="tx-val">${tx.amount_usdc.toFixed(4)}</div>
                <div className="tx-currency">USDC</div>
              </div>
            </div>
          ))
        ) : (
          <div className="empty-feed">
            [AWAITING_NETWORK_ACTIVITY]
          </div>
        )}
      </div>
      
      <div className="feed-footer">
        <p>NETWORK: ARC_TESTNET_V1</p>
        <p>AVG_LATENCY: 1840ms</p>
      </div>
    </div>
  );
}
