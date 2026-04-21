import type { DashboardSummary } from "../types";

type Props = {
  summary: DashboardSummary | null;
  isLive?: boolean;
};

export default function TransactionFeed({ summary, isLive }: Props) {
  return (
    <div className="card">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <h2 style={{ margin: 0 }}>Transaction Feed</h2>
        {isLive && (
          <div className="live-indicator">
            <span className="blink"></span>
            LIVE
          </div>
        )}
      </div>
      <div className="transaction-list">
        {summary?.latest_transactions?.length ? (
          summary.latest_transactions.map((tx) => (
            <div key={tx.id} className="transaction-item new-tx-animate">
              <div>
                <strong>{tx.id}</strong>
                <p className="tx-status-sub">
                  {tx.x402_status === "paid" ? "⚡ x402 Nanopayment" : "Settle Flow"}
                </p>
                <p className="address-link">{tx.wallet_address?.slice(0, 10)}...</p>
                {tx.tx_hash && (
                  <a href={`https://testnet.arcscan.app/tx/${tx.tx_hash}`} target="_blank" className="tx-link">
                    View on Arc
                  </a>
                )}
              </div>
              <div style={{ textAlign: 'right' }}>
                <p><strong>{tx.amount_usdc} USDC</strong></p>
                <p><span className={`status-badge ${tx.status}`}>{tx.status}</span></p>
              </div>
            </div>
          ))
        ) : (
          <p>No transactions yet.</p>
        )}
      </div>
    </div>
  );
}
