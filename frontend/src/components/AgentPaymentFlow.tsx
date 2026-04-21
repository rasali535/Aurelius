import { useEffect, useRef, useState } from "react";

type PaymentEvent = {
  id: string;
  from: string;
  to: string;
  amount: number;
  status: "pending" | "settled";
  timestamp: string;
};

type AgentNode = {
  id: string;
  label: string;
  role: string;
  x: number;
  y: number;
};

const AGENTS: AgentNode[] = [
  { id: "orchestrator", label: "ORCHESTRATOR",  role: "Master Agent",   x: 380, y: 55  },
  { id: "validator_1",  label: "VALIDATOR_1",   role: "Toxicity Guard",  x: 80,  y: 210 },
  { id: "validator_2",  label: "VALIDATOR_2",   role: "PII Shield",      x: 310, y: 210 },
  { id: "validator_3",  label: "VALIDATOR_3",   role: "Bias Detector",   x: 540, y: 210 },
  { id: "router",       label: "ARC_ROUTER",    role: "Smart Router",    x: 220, y: 370 },
  { id: "featherless",  label: "FEATHERLESS",   role: "Inference API",   x: 490, y: 370 },
];

const FLOWS = [
  { from: "orchestrator", to: "validator_1" },
  { from: "orchestrator", to: "validator_2" },
  { from: "orchestrator", to: "validator_3" },
  { from: "orchestrator", to: "router" },
  { from: "router",       to: "featherless" },
];

const MOCK_EVENTS: PaymentEvent[] = [
  { id: "e1", from: "orchestrator", to: "validator_1", amount: 0.0050, status: "settled", timestamp: new Date().toISOString() },
  { id: "e2", from: "orchestrator", to: "validator_2", amount: 0.0050, status: "settled", timestamp: new Date().toISOString() },
  { id: "e3", from: "orchestrator", to: "validator_3", amount: 0.0050, status: "settled", timestamp: new Date().toISOString() },
  { id: "e4", from: "orchestrator", to: "router",      amount: 0.0030, status: "settled", timestamp: new Date().toISOString() },
  { id: "e5", from: "router",       to: "featherless", amount: 0.0080, status: "settled", timestamp: new Date().toISOString() },
];

function getNode(id: string) {
  return AGENTS.find((a) => a.id === id);
}

type Props = { isLive?: boolean };

export default function AgentPaymentFlow({ isLive }: Props) {
  const [events, setEvents] = useState<PaymentEvent[]>(MOCK_EVENTS);
  const [activeFlow, setActiveFlow] = useState<string | null>(null);
  const idxRef = useRef(0);

  // Cycle through animated flows when live simulation is running
  useEffect(() => {
    if (!isLive) { setActiveFlow(null); return; }
    const cycle = setInterval(() => {
      const flow = FLOWS[idxRef.current % FLOWS.length];
      setActiveFlow(`${flow.from}-${flow.to}`);
      // Realistic amounts matching the validator fee schedule
      const amounts: Record<string, number> = {
        "orchestrator-validator_1": 0.005,
        "orchestrator-validator_2": 0.005,
        "orchestrator-validator_3": 0.005,
        "orchestrator-router":      0.003,
        "router-featherless":        0.008,
      };
      const amount = amounts[`${flow.from}-${flow.to}`] ?? 0.001;
      setEvents((prev) => [
        {
          id: Date.now().toString(),
          from: flow.from,
          to: flow.to,
          amount,
          status: "settled",
          timestamp: new Date().toISOString(),
        },
        ...prev.slice(0, 9),
      ]);
      idxRef.current++;
    }, 1800);
    return () => clearInterval(cycle);
  }, [isLive]);

  const totalFlow = events.reduce((sum, e) => sum + e.amount, 0);

  const agentColor = (id: string) => {
    const map: Record<string, string> = {
      orchestrator: "#00f2ff",
      validator_1:  "#7000ff",
      validator_2:  "#7000ff",
      router:       "#00ff9d",
      featherless:  "#ffae00",
    };
    return map[id] ?? "#fff";
  };

  return (
    <div className="card agent-payment-card">
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
        <h2 style={{ margin: 0, textTransform: "uppercase", letterSpacing: "0.1em", fontSize: "1rem" }}>
          Agent_Payment_Graph
        </h2>
        <div style={{ display: "flex", gap: 16, alignItems: "center" }}>
          {isLive && (
            <div className="live-indicator">
              <span className="blink"></span>
              LIVE
            </div>
          )}
          <div style={{ textAlign: "right" }}>
            <div style={{ fontFamily: "var(--terminal-font)", fontSize: "0.7rem", color: "var(--success)" }}>
              SETTLED: ${totalFlow.toFixed(4)} USDC
            </div>
            <div style={{ fontFamily: "var(--terminal-font)", fontSize: "0.6rem", color: "var(--text-muted)", marginTop: 2 }}>
              MAX/ACTION: $0.01 · ARC GAS: ~$0.000001
            </div>
          </div>
        </div>
      </div>

      {/* SVG Flow Graph */}
      <div style={{ width: "100%", overflowX: "auto" }}>
        <svg viewBox="0 0 760 500" width="100%" style={{ display: "block" }}>
          <defs>
            {/* Animated flow marker */}
            <marker id="arrowBlue" markerWidth="6" markerHeight="6" refX="3" refY="3" orient="auto">
              <path d="M0,0 L6,3 L0,6 Z" fill="rgba(0,242,255,0.6)" />
            </marker>
            <marker id="arrowGreen" markerWidth="6" markerHeight="6" refX="3" refY="3" orient="auto">
              <path d="M0,0 L6,3 L0,6 Z" fill="rgba(0,255,157,0.6)" />
            </marker>
            <filter id="glow">
              <feGaussianBlur stdDeviation="3" result="coloredBlur" />
              <feMerge><feMergeNode in="coloredBlur" /><feMergeNode in="SourceGraphic" /></feMerge>
            </filter>
          </defs>

          {/* Connection lines */}
          {FLOWS.map((flow) => {
            const src = getNode(flow.from);
            const dst = getNode(flow.to);
            if (!src || !dst) return null;
            const flowId = `${flow.from}-${flow.to}`;
            const isActive = activeFlow === flowId;
            return (
              <g key={flowId}>
                <line
                  x1={src.x} y1={src.y + 28}
                  x2={dst.x} y2={dst.y - 28}
                  stroke={isActive ? "rgba(0,242,255,0.5)" : "rgba(255,255,255,0.07)"}
                  strokeWidth={isActive ? 2 : 1}
                  strokeDasharray={isActive ? "none" : "4 6"}
                  markerEnd={isActive ? "url(#arrowBlue)" : undefined}
                  style={{ transition: "all 0.4s" }}
                  filter={isActive ? "url(#glow)" : undefined}
                />
                {/* Animated payment particle */}
                {isActive && (
                  <circle r="5" fill="var(--primary)" filter="url(#glow)">
                    <animateMotion
                      dur="1.2s"
                      repeatCount="indefinite"
                      path={`M${src.x},${src.y + 28} L${dst.x},${dst.y - 28}`}
                    />
                  </circle>
                )}
              </g>
            );
          })}

          {/* Agent nodes */}
          {AGENTS.map((agent) => {
            const color = agentColor(agent.id);
            const isActive = activeFlow?.includes(agent.id);
            return (
              <g key={agent.id} transform={`translate(${agent.x - 80}, ${agent.y - 28})`}>
                {/* Background glow when active */}
                {isActive && (
                  <rect x="-4" y="-4" width="168" height="64" rx="6"
                    fill={color} opacity="0.07" filter="url(#glow)" />
                )}
                {/* Node box */}
                <rect x="0" y="0" width="160" height="56" rx="4"
                  fill="rgba(10,10,25,0.9)"
                  stroke={isActive ? color : "rgba(255,255,255,0.08)"}
                  strokeWidth={isActive ? 1.5 : 1}
                  style={{ transition: "all 0.4s" }}
                />
                {/* Color accent bar */}
                <rect x="0" y="0" width="3" height="56" rx="2" fill={color} opacity="0.8" />

                {/* Label */}
                <text x="14" y="22" fontSize="10" fill={color}
                  fontFamily="'Fira Code', monospace" letterSpacing="0.1em">
                  {agent.label}
                </text>
                <text x="14" y="40" fontSize="9" fill="rgba(255,255,255,0.35)"
                  fontFamily="'Fira Code', monospace">
                  {agent.role}
                </text>
              </g>
            );
          })}
        </svg>
      </div>

      {/* Payment Event Log */}
      <div style={{ marginTop: 16, borderTop: "1px solid var(--panel-border)", paddingTop: 14 }}>
        <p style={{ fontSize: "0.65rem", fontFamily: "var(--terminal-font)", color: "var(--text-muted)", marginBottom: 8, letterSpacing: "0.1em" }}>
          RECENT_SETTLEMENTS
        </p>
        <div style={{ display: "flex", flexDirection: "column", gap: 6, maxHeight: 160, overflowY: "auto" }}>
          {events.map((ev) => (
            <div key={ev.id} className="payment-event-row new-tx-animate">
              <span style={{ fontFamily: "var(--terminal-font)", fontSize: "0.65rem", color: agentColor(ev.from) }}>{ev.from.toUpperCase()}</span>
              <span style={{ fontSize: "0.6rem", opacity: 0.4 }}>──▶</span>
              <span style={{ fontFamily: "var(--terminal-font)", fontSize: "0.65rem", color: agentColor(ev.to) }}>{ev.to.toUpperCase()}</span>
              <span style={{ marginLeft: "auto", fontFamily: "var(--terminal-font)", fontSize: "0.7rem", color: "var(--success)" }}>
                ${ev.amount.toFixed(4)} USDC
              </span>
              <span style={{ fontSize: "0.6rem", color: "var(--success)", marginLeft: 8 }}>✓</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
