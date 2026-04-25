import { useEffect, useState } from "react";
import type { DashboardSummary, Transaction } from "../types";

type Props = {
  summary: DashboardSummary | null;
};

export default function TransactionFeed({ summary }: Props) {
  const [localTxs, setLocalTxs] = useState<Transaction[]>([]);

  useEffect(() => {
    if (summary?.latest_transactions) {
      setLocalTxs(summary.latest_transactions);
    }
  }, [summary]);

  return (
    <div className="card transaction-feed-card">
      <div className="feed-header">
        <div className="header-left">
          <h2><span className="text-primary">03</span> SETTLEMENT_FEED</h2>
          <div className="live-indicator">
            <div className="blink"></div>
            ACTIVE_SYNC
          </div>
        </div>
        <div className="header-actions">
          <a 
            href="https://testnet.arcscan.app/" 
            target="_blank" 
            rel="noreferrer" 
            className="explorer-link-btn"
          >
            OPEN_EXPLORER
          </a>
        </div>
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
                   {tx.tx_hash && /^(0x)?[a-fA-F0-9]{40,66}$/.test(tx.tx_hash) ? (
                    <a 
                      href={`https://testnet.arcscan.app/${tx.tx_hash.length > 42 ? 'tx' : 'address'}/${tx.tx_hash.startsWith('0x') ? tx.tx_hash : '0x' + tx.tx_hash}`} 
                      target="_blank" 
                      rel="noreferrer" 
                      className="arc-link"
                      style={{ color: 'var(--primary)', opacity: 0.9 }}
                    >
                      {tx.tx_hash.length > 20 ? `${tx.tx_hash.slice(0, 20)}...` : tx.tx_hash}
                    </a>
                   ) : (
                     <span className="arc-link" style={{ opacity: 0.5, border: 'none' }}>
                       {tx.tx_hash && tx.tx_hash.toLowerCase().includes("failed") ? "TX_FAILED" : "INDEXING_ON_CHAIN"}
                     </span>
                   )}
                </div>
              </div>
              <div className="tx-amount-side">
                <div className="tx-val">
                  ${new Intl.NumberFormat('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 6 }).format(tx.amount_usdc)}
                </div>
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
