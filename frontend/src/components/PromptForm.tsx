import { useState } from "react";

type Props = {
  onRun: (prompt: string) => Promise<void>;
  onRouterRun: (task: string) => Promise<void>;
  onBatchRun: () => Promise<void>;
  loading: boolean;
};

export default function PromptForm({ onRun, onRouterRun, onBatchRun, loading }: Props) {
  const [prompt, setPrompt] = useState("Explain the benefits of decentralized identity.");
  const [activeTab, setActiveTab] = useState<"guardrail" | "router">("guardrail");

  return (
    <div className="card">
      <div style={{ display: 'flex', gap: '20px', marginBottom: '24px', borderBottom: '1px solid rgba(255,255,255,0.1)' }}>
        <h2 
          onClick={() => setActiveTab("guardrail")}
          style={{ cursor: 'pointer', opacity: activeTab === 'guardrail' ? 1 : 0.5, borderBottom: activeTab === 'guardrail' ? '2px solid #3d7eff' : 'none', paddingBottom: '10px', marginBottom: 0 }}
        >
          🛡️ Guardrail Agent
        </h2>
        <h2 
          onClick={() => setActiveTab("router")}
          style={{ cursor: 'pointer', opacity: activeTab === 'router' ? 1 : 0.5, borderBottom: activeTab === 'router' ? '2px solid #3d7eff' : 'none', paddingBottom: '10px', marginBottom: 0 }}
        >
          🔀 Smart Router
        </h2>
      </div>

      <textarea
        className="textarea"
        rows={6}
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
        placeholder={activeTab === 'guardrail' ? "Enter a prompt to validate..." : "Enter a task to route to Featherless..."}
      />
      
      <div className="actions">
        {activeTab === 'guardrail' ? (
          <>
            <button disabled={loading} onClick={() => onRun(prompt)}>
              {loading ? "Processing..." : "🛡️ Run Guardrail Check"}
            </button>
            <button className="secondary" disabled={loading} onClick={onBatchRun}>
              {loading ? "Running..." : "📊 Run Stress Test (50+ TX)"}
            </button>
          </>
        ) : (
          <button disabled={loading} onClick={() => onRouterRun(prompt)}>
            {loading ? "Routing & Settling..." : "🔀 Route Task (Auto-Settle USDC)"}
          </button>
        )}
      </div>
    </div>
  );
}
