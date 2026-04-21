import { useState, useEffect } from "react";
import { api } from "../services/api";

type QueryResult = {
  results: any[];
  count: number;
};

export default function MongoPlayground() {
  const [collections, setCollections] = useState<string[]>([]);
  const [selectedColl, setSelectedColl] = useState("");
  const [queryType, setQueryType] = useState<"find" | "aggregate">("find");
  const [queryString, setQueryString] = useState('{\n  "filter": {},\n  "limit": 10\n}');
  const [results, setResults] = useState<QueryResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchCollections = async () => {
      try {
        const res = await api.get("/playground/collections");
        setCollections(res.data.collections);
        if (res.data.collections.length > 0) {
          setSelectedColl(res.data.collections[0]);
        }
      } catch (err) {
        console.error("Failed to fetch collections", err);
      }
    };
    fetchCollections();
  }, []);

  const handleExecute = async () => {
    setLoading(true);
    setError(null);
    try {
      const params = JSON.parse(queryString);
      const res = await api.post("/playground/query", {
        collection: selectedColl,
        query_type: queryType,
        params,
      });
      setResults(res.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || "Invalid JSON or Query Error");
    } finally {
      setLoading(false);
    }
  };

  const setTemplate = (type: "find" | "aggregate") => {
    setQueryType(type);
    if (type === "find") {
      setQueryString('{\n  "filter": {},\n  "limit": 5,\n  "sort": { "settled_at": -1 }\n}');
    } else {
      setQueryString('{\n  "pipeline": [\n    { "$group": { "_id": "$status", "count": { "$sum": 1 } } }\n  ]\n}');
    }
  };

  return (
    <div className="card mongo-playground">
      <div className="playground-header">
        <h3 style={{ fontSize: "0.9rem", color: "var(--primary)", letterSpacing: "0.1em" }}>
          DB_FORGE_EXPLORER
        </h3>
        <div className="collection-badge">CONNECTED: {selectedColl.toUpperCase()}</div>
      </div>

      <div className="playground-controls">
        <select 
          value={selectedColl} 
          onChange={(e) => setSelectedColl(e.target.value)}
          className="cyber-select"
        >
          {collections.map(c => <option key={c} value={c}>{c}</option>)}
        </select>

        <div className="query-type-toggle">
          <button 
            className={queryType === "find" ? "active" : ""} 
            onClick={() => setTemplate("find")}
          >
            FIND
          </button>
          <button 
            className={queryType === "aggregate" ? "active" : ""} 
            onClick={() => setTemplate("aggregate")}
          >
            AGGREGATE
          </button>
        </div>
      </div>

      <div className="editor-container">
        <textarea
          value={queryString}
          onChange={(e) => setQueryString(e.target.value)}
          placeholder="Enter JSON query parameters..."
          className="cyber-textarea"
          spellCheck={false}
        />
        <button 
          className="cyber-btn execute-btn" 
          onClick={handleExecute}
          disabled={loading}
        >
          {loading ? "EXECUTING..." : "RUN_QUERY"}
        </button>
      </div>

      {error && <div className="playground-error">{error}</div>}

      <div className="results-container">
        <div className="results-meta">
          <span>OUTPUT_BUFFER</span>
          {results && <span>DOC_COUNT: {results.count}</span>}
        </div>
        <pre className="results-pre">
          {results ? JSON.stringify(results.results, null, 2) : "// Awaiting input command..."}
        </pre>
      </div>

      <style>{`
        .mongo-playground {
          padding: 20px;
          display: flex;
          flex-direction: column;
          gap: 15px;
          background: rgba(10, 10, 15, 0.8) !important;
          border: 1px solid var(--primary-low) !important;
        }
        .playground-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          border-bottom: 1px solid rgba(0, 255, 255, 0.1);
          padding-bottom: 10px;
        }
        .collection-badge {
          font-size: 0.65rem;
          color: var(--success);
          font-family: var(--terminal-font);
        }
        .playground-controls {
          display: flex;
          gap: 10px;
        }
        .cyber-select {
          background: #0a0a0f;
          color: var(--primary);
          border: 1px solid var(--primary-low);
          padding: 5px 10px;
          font-family: var(--terminal-font);
          font-size: 0.75rem;
          outline: none;
        }
        .query-type-toggle {
          display: flex;
          background: #0a0a0f;
          border: 1px solid var(--primary-low);
        }
        .query-type-toggle button {
          background: transparent;
          border: none;
          color: var(--primary-low);
          font-size: 0.7rem;
          padding: 5px 12px;
          cursor: pointer;
        }
        .query-type-toggle button.active {
          background: var(--primary);
          color: black;
          font-weight: bold;
        }
        .editor-container {
          position: relative;
        }
        .cyber-textarea {
          width: 100%;
          height: 120px;
          background: #050507;
          color: #a0a0a0;
          border: 1px solid var(--primary-low);
          font-family: var(--terminal-font);
          font-size: 0.8rem;
          padding: 10px;
          resize: vertical;
          outline: none;
        }
        .execute-btn {
          position: absolute;
          bottom: 10px;
          right: 10px;
          padding: 5px 15px !important;
          font-size: 0.7rem !important;
        }
        .results-container {
          background: #050507;
          border: 1px solid rgba(255, 255, 255, 0.05);
          height: 250px;
          display: flex;
          flex-direction: column;
        }
        .results-meta {
          background: rgba(255, 255, 255, 0.03);
          padding: 5px 10px;
          font-size: 0.6rem;
          color: var(--primary-low);
          display: flex;
          justify-content: space-between;
          font-family: var(--terminal-font);
        }
        .results-pre {
          padding: 10px;
          font-size: 0.75rem;
          overflow: auto;
          flex: 1;
          color: #00ff9f;
          margin: 0;
        }
        .playground-error {
          color: var(--error);
          font-size: 0.7rem;
          font-family: var(--terminal-font);
        }
      `}</style>
    </div>
  );
}
