import { useState } from "react";

type Props = {
  onRun: (prompt: string) => Promise<void>;
  onBatchRun: () => Promise<void>;
  loading: boolean;
};

export default function PromptForm({ onRun, onBatchRun, loading }: Props) {
  const [prompt, setPrompt] = useState("Can aspirin cure viral infections?");

  return (
    <div className="card">
      <h2>Requester Agent</h2>
      <textarea
        className="textarea"
        rows={6}
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
        placeholder="Enter a prompt"
      />
      <div className="actions">
        <button disabled={loading} onClick={() => onRun(prompt)}>
          {loading ? "Running..." : "Run Single Prompt"}
        </button>
        <button disabled={loading} onClick={onBatchRun}>
          {loading ? "Running..." : "Run 50+ Transaction Demo"}
        </button>
      </div>
    </div>
  );
}
