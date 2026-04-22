import React, { memo } from 'react';

const AgentNetworkGraphic = memo(function AgentNetworkGraphic() {
  return (
    <div className="network-graphic-container">
      <svg width="100%" height="100%" viewBox="0 0 800 400" fill="none" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <radialGradient id="nodeGlow" cx="50%" cy="50%" r="50%" fx="50%" fy="50%">
            <stop offset="0%" stopColor="var(--primary)" stopOpacity="0.6" />
            <stop offset="100%" stopColor="var(--primary)" stopOpacity="0" />
          </radialGradient>
          <linearGradient id="streamGradient" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="var(--primary)" stopOpacity="0" />
            <stop offset="50%" stopColor="var(--secondary)" stopOpacity="0.5" />
            <stop offset="100%" stopColor="var(--primary)" stopOpacity="0" />
          </linearGradient>
        </defs>
        
        {/* Animated Streams */}
        {[...Array(6)].map((_, i) => (
          <path 
            key={`path-${i}`}
            d={`M ${100 + i * 120} 200 Q ${200 + i * 120} ${100 + (i%2)*200} ${300 + i * 120} 200`}
            stroke="url(#streamGradient)"
            strokeWidth="2"
            fill="none"
            className="animate-path"
            style={{ animationDelay: `${i * 0.5}s` }}
          />
        ))}

        {/* Nodes */}
        {[
          { x: 100, y: 200, size: 20 },
          { x: 250, y: 120, size: 15 },
          { x: 250, y: 280, size: 15 },
          { x: 400, y: 200, size: 25 },
          { x: 550, y: 120, size: 15 },
          { x: 550, y: 280, size: 15 },
          { x: 700, y: 200, size: 20 },
        ].map((node, i) => (
          <React.Fragment key={`node-${i}`}>
            <circle cx={node.x} cy={node.y} r={node.size * 2} fill="url(#nodeGlow)" className="node-pulse" />
            <circle cx={node.x} cy={node.y} r={node.size / 2} fill="white" fillOpacity="0.8" />
            <circle cx={node.x} cy={node.y} r={node.size} stroke="var(--primary)" strokeWidth="1" strokeDasharray="4 2" />
          </React.Fragment>
        ))}
      </svg>
      
      <style>{`
        .network-graphic-container {
          width: 100%;
          height: 100%;
          max-width: 800px;
          margin: 0 auto;
          position: relative;
        }
        .animate-path {
          stroke-dasharray: 1000;
          stroke-dashoffset: 1000;
          animation: draw 8s linear infinite;
        }
        @keyframes draw {
          to { stroke-dashoffset: 0; }
        }
        .node-pulse {
          animation: pulseNode 4s ease-in-out infinite;
        }
        @keyframes pulseNode {
          0%, 100% { transform: scale(1); opacity: 0.4; }
          50% { transform: scale(1.1); opacity: 0.7; }
        }
      `}</style>
    </div>
  );
});

export default AgentNetworkGraphic;
