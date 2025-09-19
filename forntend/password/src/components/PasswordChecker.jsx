import React, { useEffect, useMemo, useState } from "react";
import { Eye, EyeOff } from "lucide-react"; // icons


function StrengthBar({ score }) {
  const width = ((score + 1) / 5) * 100; // map 0..4 to 20..100 (visual)
  const colorClass = score <= 1 ? "bg-red-500" : score === 2 ? "bg-amber-500" : "bg-green-500";
  return (
    <div className="w-full bg-[rgba(0,0,0,0.06)] rounded h-3 overflow-hidden mt-2">
      <div className={`h-full ${colorClass}`} style={{ width: `${width}%` }} />
    </div>
  );
}

function SuggestionList({ suggestions }) {
  return (
    <ul className="list-disc pl-5 space-y-1">
      {suggestions.map((s, i) => (
        <li key={i} className="text-sm">{s}</li>
      ))}
    </ul>
  );
}

function useDebounced(value, ms=350) {
  const [v, setV] = useState(value);
  useEffect(() => {
    const id = setTimeout(() => setV(value), ms);
    return () => clearTimeout(id);
  }, [value, ms]);
  return v;
}

export default function PasswordChecker() {
  const [password, setPassword] = useState("");
  const debounced = useDebounced(password, 300);
  const [loading, setLoading] = useState(false);
  const [analysis, setAnalysis] = useState(null);
  const [ai, setAi] = useState(null);
  const [error, setError] = useState(null);
  const [generated, setGenerated] = useState([]);

  const backendBase = import.meta.env.VITE_API_BASE || "http://localhost:8000"; // configure VITE_API_BASE during dev
  const [showPassword, setShowPassword] = useState(false);

  useEffect(() => {
    if (debounced === "") {
      setAnalysis(null);
      setAi(null);
      setError(null);
      return;
    }
    let abort = false;
    const doAnalyze = async () => {
      setLoading(true);
      setError(null);
      try {
        const resp = await fetch(`${backendBase}/api/analyze`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ password: debounced }),
        });
        if (!resp.ok) {
          const j = await resp.json().catch(() => ({}));
          throw new Error(j.error || resp.statusText || "Server error");
        }
        const body = await resp.json();
        if (!abort) {
          setAnalysis(body.analysis);
          setAi(body.ai);
          setGenerated(body.ai?.alternatives || []);
        }
      } catch (e) {
        if (!abort) setError(e.message);
      } finally {
        if (!abort) setLoading(false);
      }
    };
    doAnalyze();
    return () => { abort = true; };
  }, [debounced, backendBase]);

  const score = analysis?.score ?? 0;

  const localAlternatives = useMemo(() => {
    if (generated && generated.length) return generated;
    // client-side fallback generator (uses crypto):
    function gen(len=16) {
      const chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()-_=+[]{}|:;,.<>/?";
      const arr = new Uint32Array(len);
      crypto.getRandomValues(arr);
      return Array.from(arr).map(n => chars[n % chars.length]).join('');
    }
    return [gen(16), gen(16), gen(16)];
  }, [generated]);

  const handleGenerateClick = async (len=16) => {
    try {
      // Prefer backend generate endpoint (server-side crypto)
      const resp = await fetch(`${backendBase}/api/generate?length=${len}`);
      if (resp.ok) {
        const { password } = await resp.json();
        setPassword(password);
      } else {
        // fallback to client generation
        setPassword(localAlternatives[0]);
      }
    } catch {
      setPassword(localAlternatives[0]);
    }
  };

  return (
    <div>
      <label className="block text-sm mb-2">Enter password to evaluate</label>
      <div className="flex gap-2 items-center relative w-full">
  <input
    value={password}
    onChange={(e) => setPassword(e.target.value)}
    type={showPassword ? "text" : "password"}
    placeholder="Type a password or paste one"
    className="flex-1 p-3 rounded border focus:outline-none pr-10"
    aria-label="password input"
  />

  {/* Toggle visibility button */}
  <button
    type="button"
    className="absolute right-28 top-1/2 -translate-y-1/2 text-gray-500"
    onClick={() => setShowPassword(!showPassword)}
  >
    {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
  </button>

  {/* Generate button stays as is */}
  <button
    onClick={() => handleGenerateClick(16)}
    className="btn px-4 py-2 rounded"
  >
    Generate
  </button>
</div>

      <div className="mt-4">
        <div className="flex justify-between items-center">
          <div>
            
            <div className="text-lg font-semibold">{ai?.classification ?? (["Very weak","Weak","Moderate","Strong","Very strong"][score] ?? "—")}</div>
          </div>
          <div className="text-sm text-[color:rgb(var(--muted))]">
            {analysis ? `Entropy: ${analysis.entropy} bits • Length: ${analysis.length}` : (loading ? "Checking..." : "")}
          </div>
        </div>

        <StrengthBar score={score} />

        <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <h3 className="font-medium mb-2">Smart Suggestions</h3>
            {loading && <div className="text-sm text-[color:rgb(var(--muted))]">Analyzing…</div>}
            {error && <div className="text-sm text-red-600">Error: {error}</div>}
            {!loading && ai && (
              <>
                <div className="text-sm mb-2">{ai.explanation}</div>
                <SuggestionList suggestions={ai.suggestions || []} />
              </>
            )}
            {!loading && !ai && !error && (
              <div className="text-sm text-[color:rgb(var(--muted))]">No analysis yet — type a password.</div>
            )}
          </div>

          <div>
            <h3 className="font-medium mb-2">Alternative Strong Passwords</h3>
            <div className="space-y-2">
              {(ai?.alternatives ?? localAlternatives).map((p, idx) => (
                <div key={idx} className="flex items-center justify-between p-2 rounded border">
                  <div className="truncate text-sm">{p}</div>
                  <div className="flex gap-2">
                    <button className="px-3 py-1 rounded border" onClick={() => navigator.clipboard?.writeText(p)}>Copy</button>
                    <button
                      className="px-3 py-1 rounded btn"
                      onClick={() => setPassword(p)}
                    >
                      Use
                    </button>
                  </div>
                </div>
              ))}
            </div>

            <div className="mt-4 text-sm">
              <button className="px-3 py-1 rounded border" onClick={() => handleGenerateClick(20)}>Generate 20-char</button>
              <button className="ml-2 px-3 py-1 rounded border" onClick={() => handleGenerateClick(32)}>Generate 32-char</button>
            </div>
          </div>
        </div>

      </div>

              
    </div>
  );
}
