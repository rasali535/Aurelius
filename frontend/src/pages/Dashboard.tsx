import { useEffect, useState } from "react";
import PromptForm from "../components/PromptForm";
import MetricsCards from "../components/MetricsCards";
import ValidatorPanel from "../components/ValidatorPanel";
import TransactionFeed from "../components/TransactionFeed";
import { api } from "../services/api";
import { DashboardSummary, PromptRunResponse } from "../types";

export default function Dashboard() {
  const [loading, setLoading] = useState(false);
  const [run, setRun] = useState<PromptRunResponse | null>(null);
  const [summary, setSummary] = useState<DashboardSummary | null>(null);

  const fetchSummary = async () => {
    try {
      const res = await api.get("/dashboard/summary");
      setSummary(res.data);
    } catch (err) {
      console.error("Failed to fetch dashboard summary", err);
    }
  };

  useEffect(() => {
    fetchSummary();
    // Poll for updates every 10 seconds
    const interval = setInterval(fetchSummary, 10000);
    return () => clearInterval(interval);
  }, []);

  const handleRun = async (prompt: string) => {
    setLoading(true);
    try {
      const res = await api.post("/run-prompt", { prompt });
      setRun(res.data);
      await fetchSummary();
    } catch (err) {
      console.error("Run prompt failed", err);
    } finally {
      setLoading(false);
    }
  };

  const handleBatchRun = async () => {
    setLoading(true);
    try {
      await api.post("/run-demo-batch");
      await fetchSummary();
    } catch (err) {
      console.error("Batch run failed", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page">
      <header>
        <h1>Aurelius</h1>
        <p className="subtitle">
          Autonomous LLM guardrail network with sub-cent agent-to-agent payments.
        </p>
      </header>

      <MetricsCards summary={summary} />
      
      <PromptForm onRun={handleRun} onBatchRun={handleBatchRun} loading={loading} />

      <div className="grid-two">
        <ValidatorPanel run={run} />
        <TransactionFeed summary={summary} />
      </div>
    </div>
  );
}
