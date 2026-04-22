import type { PromptRunResponse } from "../types";

type Props = {
  run: PromptRunResponse | null;
  routerResults?: any[];
};

export default function ValidatorPanel({ run, routerResults = [] }: Props) {
  if (routerResults.length > 0) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
        {routerResults.map((res, idx) => (
          <div key={res.run_id || idx} className="card fade-in" style={{ margin: 0 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
              <h2 style={{ margin: 0, textTransform: 'uppercase', letterSpacing: '0.1em' }}>Neural_Router_Output</h2>
              <span className="status-badge settled" style={{ background: 'var(--success)', color: 'var(--background)', padding: '4px 12px', borderRadius: '4px', fontSize: '0.7rem', fontWeight: 700 }}>
                SETTLED: ${res.price_usdc} USDC
              </span>
            </div>
            
            <div style={{ marginBottom: '24px', borderLeft: '2px solid var(--primary)', paddingLeft: '20px' }}>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.8rem', fontFamily: 'var(--terminal-font)', marginBottom: '8px' }}>
                [EXECUTING_MODEL]: {res.model_id}
              </p>
              <div style={{ fontSize: '1.1rem', lineHeight: '1.6', color: 'var(--text-main)' }}>
                {res.output}
              </div>
            </div>

            <div className="reasoning-block" style={{ background: 'rgba(0, 242, 255, 0.05)', padding: '15px', borderRadius: '4px', border: '1px dashed var(--panel-border)' }}>
              <p style={{ fontSize: '0.75rem', fontFamily: 'var(--terminal-font)', margin: 0 }}>
                <span style={{ color: 'var(--primary)' }}>[REASONING_ENGINE]:</span> {res.reasoning}
              </p>
            </div>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="card">
      <h2 style={{ textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: '20px' }}>Validator_Swarm_Diagnostics</h2>
      {!run ? (
        <div style={{ opacity: 0.3, padding: '40px 0', textAlign: 'center' }}>
          <p>[AWAITING_SEQUENCE_INIT]</p>
        </div>
      ) : (
        <>
          <div className="run-summary" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px', marginBottom: '30px', fontSize: '0.8rem', fontFamily: 'var(--terminal-font)' }}>
            <div className="diag-bit"><span style={{ color: 'var(--text-muted)' }}>RUN_ID:</span> {run.run_id}</div>
            <div className="diag-bit"><span style={{ color: 'var(--text-muted)' }}>STATUS:</span> {run.final_status}</div>
            <div className="diag-bit"><span style={{ color: 'var(--text-muted)' }}>COST:</span> {run.total_cost_usdc} USDC</div>
            <div className="diag-bit"><span style={{ color: 'var(--text-muted)' }}>NODES:</span> {run.validator_count}</div>
          </div>

          <div className="validator-list" style={{ display: 'grid', gap: '15px' }}>
            {run.results.map((item) => (
              <div className="validator-card" key={item.validator_id + item.check_type} style={{ background: 'rgba(255,255,255,0.03)', padding: '15px', border: '1px solid rgba(0,242,255,0.1)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                  <h3 style={{ margin: 0, fontSize: '0.9rem', color: 'var(--primary)' }}>{item.check_type.toUpperCase()}</h3>
                  <span style={{ fontSize: '0.7rem', color: item.status === 'passed' ? 'var(--success)' : 'var(--error)' }}>
                    [{item.status.toUpperCase()}]
                  </span>
                </div>
                <p style={{ fontSize: '0.8rem', margin: '4px 0', opacity: 0.8 }}>{item.reason}</p>
                <div style={{ marginTop: '10px', fontSize: '0.7rem', opacity: 0.6, display: 'flex', justifyContent: 'space-between' }}>
                   <span>LATENCY: {item.response_time_ms}ms</span>
                   <span>FEE: {item.unit_price} USDC</span>
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
