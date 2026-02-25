"use client";

import { useState } from "react";
import ReportView from "./components/ReportView";
import SourceGrid from "./components/SourceGrid";

export default function Home() {
  const [query, setQuery] = useState("");
  const [isSearching, setIsSearching] = useState(false);
  const [logs, setLogs] = useState<string[]>([]);
  const [report, setReport] = useState<string | null>(null);
  const [sources, setSources] = useState<any[]>([]);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setIsSearching(true);
    setReport(null);
    setSources([]);

    // Show incremental log steps while the real API call runs in the background
    setLogs(["Initializing Tavily Search..."]);

    // Kick off the real API call
    const apiPromise = fetch(`http://localhost:8000/research?query=${encodeURIComponent(query)}`, {
      method: "POST",
    }).then(res => {
      if (!res.ok) throw new Error(`API error: ${res.status}`);
      return res.json();
    });

    // Show log progression while waiting
    try {
      await new Promise(r => setTimeout(r, 1500));
      setLogs(prev => [...prev, "Browsing top sources via Playwright..."]);
      await new Promise(r => setTimeout(r, 1500));
      setLogs(prev => [...prev, "Synthesizing report with LLM..."]);

      // Await the real result
      const data = await apiPromise;

      setReport(data.summary);
      setSources(data.sources || []);
      setIsSearching(false);
    } catch (err: any) {
      console.error(err);
      setLogs(prev => [...prev, `❌ Error: ${err.message}`]);
      setIsSearching(false);
    }
  };

  return (
    <main className={`min-h-screen flex flex-col items-center p-6 relative transition-all duration-1000 ${report ? 'pt-12' : 'justify-center'}`}>
      {/* Background Decor */}
      <div className="fixed top-[-10%] left-[-10%] w-[40%] h-[40%] bg-purple-600/10 blur-[120px] rounded-full pointer-events-none" />
      <div className="fixed bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-blue-600/10 blur-[120px] rounded-full pointer-events-none" />

      <div className={`w-full max-w-3xl z-10 transition-all duration-700 ${report ? 'scale-90 opacity-80 backdrop-blur-sm' : 'scale-100 opacity-100'}`}>
        {!report && (
          <h1 className="text-5xl font-bold text-center mb-8 gradient-text animate-in fade-in duration-1000">
            Personal AI Researcher
          </h1>
        )}

        <form onSubmit={handleSearch} className="glass p-2 flex gap-2 mb-8 focus-within:ring-2 ring-purple-500/50 transition-all shadow-2xl">
          <input
            type="text"
            className="flex-1 bg-transparent border-none outline-none px-4 py-3 text-lg text-white placeholder-slate-500"
            placeholder="Search anything deep... (e.g. GPU Market analysis)"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <button
            type="submit"
            disabled={isSearching}
            className="bg-[#7c3aed] hover:bg-[#6d28d9] text-white px-8 py-3 rounded-xl font-semibold transition-all shadow-lg shadow-purple-500/20 disabled:opacity-50"
          >
            {isSearching ? "Searching..." : "Research"}
          </button>
        </form>

        {isSearching && (
          <div className="glass p-6 animate-in fade-in slide-in-from-bottom-4 duration-700">
            <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-widest mb-4">
              Agent Activity Log
            </h3>
            <div className="space-y-3">
              {logs.map((log, i) => (
                <div key={i} className="flex items-center gap-3 text-slate-300">
                  <div className={`w-2 h-2 rounded-full ${i === logs.length - 1 ? 'bg-purple-500 pulse' : 'bg-slate-600'}`} />
                  <span className="font-mono text-sm">{log}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {report && (
        <div className="w-full max-w-4xl z-10 animate-in fade-in slide-in-from-bottom-8 duration-1000 pb-20">
          <ReportView content={report} />
          <SourceGrid sources={sources} />

          <button
            onClick={() => { setReport(null); setQuery(""); }}
            className="mt-12 mx-auto block text-slate-500 hover:text-white transition-colors text-sm font-medium"
          >
            ← Start New Research
          </button>
        </div>
      )}
    </main>
  );
}
