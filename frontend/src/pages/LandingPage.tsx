type Props = {
  onEnterApp: () => void;
};

export default function LandingPage({ onEnterApp }: Props) {
  return (
    <div className="page fade-in">
      <nav className="nav-bar">
        <a href="#" className="logo-text">AURELIUS</a>
        <button className="secondary" onClick={onEnterApp}>Launch Terminal →</button>
      </nav>

      <section className="landing-hero">
        <div className="hero-content">
          <h1 className="hero-title">Build the Agentic Economy on Arc</h1>
          <p className="subtitle">
            Autonomous workflows powered by Programmable USDC and gasless Nanopayments. 
            The new standard for machine-to-machine commerce.
          </p>
          <button style={{ padding: '18px 40px', fontSize: '1.25rem' }} onClick={onEnterApp}>
            Get Started with Aurelius
          </button>
        </div>
      </section>

      <section className="tracks">
        <div style={{ textAlign: 'center', marginBottom: '48px' }}>
          <h2 style={{ fontSize: '2.5rem', marginBottom: '16px' }}>Specialized Tracks</h2>
          <p className="subtitle" style={{ margin: '0 auto' }}>Choose your path in the autonomous value economy.</p>
        </div>

        <div className="track-grid">
          <div className="card track-card">
            <h3>🪙 Per-API Monetization</h3>
            <p className="text-muted">
              Build an API that charges per request using USDC. Demonstrate viable per-call 
              pricing at high frequency without subscription overhead.
            </p>
          </div>
          <div className="card track-card">
            <h3>🤖 Agent-to-Agent Loop</h3>
            <p className="text-muted">
              Create autonomous agents that pay and receive value in real time. 
              Pure machine-to-machine commerce without custodial control.
            </p>
          </div>
          <div className="card track-card">
            <h3>🧮 Usage-Based Billing</h3>
            <p className="text-muted">
              Design compute-intensive applications that charge per query or per task. 
              Real-time settlement aligned to actual resource usage.
            </p>
          </div>
          <div className="card track-card">
            <h3>🛒 Micro-Commerce Flow</h3>
            <p className="text-muted">
               Build experiences where logic and value are triggered per interaction. 
               Transaction values ≤ $0.01 made possible by Arc.
            </p>
          </div>
        </div>
      </section>

      <section className="proof-section">
        <div className="proof-grid">
          <div>
            <h2 style={{ fontSize: '3rem', lineHeight: '1.1', marginBottom: '24px' }}>The Economic Proof.</h2>
            <p className="subtitle">
              Traditional gas fees ($0.05 - $0.50) make agentic nanopayments impossible. 
              At a $0.005 per-validation price point, traditional networks incur a 1000% loss per transaction.
            </p>
            <div style={{ marginTop: '32px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '12px' }}>
                 <span style={{ color: 'var(--success)', fontWeight: 'bold' }}>✓</span> 
                 <span>Real per-action pricing (≤ $0.01)</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '12px' }}>
                 <span style={{ color: 'var(--success)', fontWeight: 'bold' }}>✓</span> 
                 <span>50+ On-chain Transactions Demo</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                 <span style={{ color: 'var(--success)', fontWeight: 'bold' }}>✓</span> 
                 <span>Gasless X402 Settlement via Circle</span>
              </div>
            </div>
          </div>

          <div className="comparison-card success-proof fade-in">
             <h3 style={{ marginBottom: '20px' }}>Arc + Aurelius Economy</h3>
             <div style={{ fontSize: '1.1rem', marginBottom: '32px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '12px', marginBottom: '12px' }}>
                  <span>Price per Action:</span>
                  <span style={{ color: 'var(--success)' }}>$0.005 USDC</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '12px', marginBottom: '12px' }}>
                  <span>Network Fee:</span>
                  <span style={{ color: 'var(--success)' }}>$0.0001 USDC</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontWeight: 'bold' }}>
                  <span>Net Margin:</span>
                  <span style={{ color: 'var(--success)' }}>+98%</span>
                </div>
             </div>
             <p style={{ fontSize: '0.9rem', color: 'rgba(255,255,255,0.6)' }}>
                *This is the only model that achieves positive unit economics for high-frequency AI agent tasks.
             </p>
          </div>
        </div>
      </section>

      <footer style={{ padding: '60px 0', textAlign: 'center', opacity: 0.5 }}>
        <p>&copy; 2026 Aurelius Layer. Powered by Circle and Arc.</p>
      </footer>
    </div>
  );
}
