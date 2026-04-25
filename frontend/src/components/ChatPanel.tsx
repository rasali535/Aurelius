import React, { useState, useEffect, useRef } from 'react';
import { api } from '../services/api';

interface Message {
  role: 'user' | 'ai';
  content: string;
  timestamp: string;
}

export default function ChatPanel() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userMsg: Message = {
      role: 'user',
      content: input,
      timestamp: new Date().toLocaleTimeString()
    };

    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      // Send the last few messages for context
      const history = messages.slice(-5).map(m => ({
        role: m.role === 'ai' ? 'assistant' : 'user',
        content: m.content
      }));

      const res = await api.post('/chat/message', {
        message: input,
        history: history
      });

      const aiMsg: Message = {
        role: 'ai',
        content: res.data.response,
        timestamp: new Date().toLocaleTimeString()
      };

      setMessages(prev => [...prev, aiMsg]);
    } catch (err) {
      console.error("Chat error:", err);
      setMessages(prev => [...prev, {
        role: 'ai',
        content: "COMMUNICATION_ERROR: LINK_STABILITY_CRITICAL. Please retry uplink.",
        timestamp: new Date().toLocaleTimeString()
      }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card chat-panel-card" style={{ display: 'flex', flexDirection: 'column', height: '100%', minHeight: '400px' }}>
      <div className="ticker-header" style={{ marginBottom: '15px' }}>
        <span style={{ fontFamily: "var(--terminal-font)", fontSize: "0.8rem", color: "var(--primary)", letterSpacing: "0.15em" }}>
          SECURE_UPLINK_CHAT_V2.0
        </span>
        <div className="live-indicator">
          <span className={loading ? "blink" : ""}></span>
          {loading ? "ENCRYPTING" : "ENCRYPTED"}
        </div>
      </div>

      <div 
        ref={scrollRef}
        className="chat-messages-container" 
        style={{ 
          flex: 1, 
          overflowY: 'auto', 
          padding: '10px',
          background: 'rgba(0, 0, 0, 0.2)',
          borderRadius: '4px',
          fontFamily: 'var(--terminal-font)',
          fontSize: '0.85rem',
          display: 'flex',
          flexDirection: 'column',
          gap: '12px',
          marginBottom: '15px'
        }}
      >
        {messages.length === 0 && (
          <div style={{ color: 'var(--text-muted)', opacity: 0.5, textAlign: 'center', marginTop: '20%' }}>
            [AWAITING_COMMUNICATION_REQUEST...]
          </div>
        )}
        {messages.map((m, i) => (
          <div key={i} style={{ 
            display: 'flex', 
            flexDirection: 'column', 
            alignItems: m.role === 'user' ? 'flex-end' : 'flex-start' 
          }}>
            <div style={{ 
              maxWidth: '85%', 
              padding: '10px 14px', 
              borderRadius: '4px',
              background: m.role === 'user' ? 'rgba(0, 242, 255, 0.1)' : 'rgba(255, 0, 187, 0.05)',
              border: `1px solid ${m.role === 'user' ? 'rgba(0, 242, 255, 0.2)' : 'rgba(255, 0, 187, 0.2)'}`,
              color: m.role === 'user' ? 'var(--primary)' : 'var(--secondary)',
              boxShadow: m.role === 'user' ? '0 0 10px rgba(0, 242, 255, 0.05)' : 'none'
            }}>
              <div style={{ fontSize: '0.65rem', opacity: 0.6, marginBottom: '4px' }}>
                {m.role === 'user' ? 'OPERATOR' : 'AURELIUS_ORCHESTRATOR'}
              </div>
              <div style={{ whiteSpace: 'pre-wrap', lineHeight: '1.4' }}>
                {m.content}
              </div>
            </div>
            <div style={{ fontSize: '0.6rem', opacity: 0.4, marginTop: '4px' }}>{m.timestamp}</div>
          </div>
        ))}
      </div>

      <div className="chat-input-row" style={{ display: 'flex', gap: '10px' }}>
        <input 
          type="text" 
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSend()}
          placeholder="SEND_COMMAND_TO_ORCHESTRATOR..."
          className="cyber-input"
          style={{ 
            flex: 1, 
            background: 'rgba(0, 0, 0, 0.3)',
            border: '1px solid rgba(0, 242, 255, 0.3)',
            color: 'var(--primary)',
            padding: '12px',
            fontFamily: 'var(--terminal-font)',
            borderRadius: '4px',
            outline: 'none'
          }}
        />
        <button 
          className="cyber-btn primary-glow" 
          onClick={handleSend}
          disabled={loading}
          style={{ padding: '0 20px', fontSize: '0.8rem' }}
        >
          SEND
        </button>
      </div>
    </div>
  );
}
