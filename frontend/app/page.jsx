"use client";

// "use client" tells Next.js this component runs in the browser, not on the
// server - required because we use useState and onClick, which only exist
// client-side. Server components (the default in Next.js's App Router)
// can't use either.

import { useState } from "react";

// Change this if your FastAPI backend runs somewhere other than the default.
const API_URL = "http://127.0.0.1:8000";

export default function Home() {
  // useState gives us a piece of memory that persists between renders, plus
  // a setter function that tells React "re-render with this new value."
  // question/setQuestion is a classic "controlled input" pair - the input
  // box's value is always exactly whatever `question` holds.
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [answer, setAnswer] = useState(null);
  const [sources, setSources] = useState([]);
  const [error, setError] = useState(null);

  async function handleAsk(e) {
    e.preventDefault(); // stop the browser's default "reload the page on submit" behavior

    if (!question.trim()) return;

    setLoading(true);
    setError(null);
    setAnswer(null);

    try {
      const response = await fetch(`${API_URL}/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
      });

      if (!response.ok) {
        throw new Error(`Server responded with ${response.status}`);
      }

      const data = await response.json();
      setAnswer(data.answer);
      setSources(data.sources);
    } catch (err) {
      setError(
        "Couldn't reach the archive. Is the backend server running on port 8000?"
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="page">
      <header className="masthead">
        <span className="eyebrow">Brightpath Consulting — Pilot</span>
        <h1>DocuChat</h1>
        <p className="subtitle">Ask a question across the document archive.</p>
      </header>

      <form className="ask-form" onSubmit={handleAsk}>
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="e.g. What did we recommend for the 2022 retail supply-chain client?"
          className="ask-input"
        />
        <button type="submit" className="ask-button" disabled={loading}>
          {loading ? "Searching…" : "Ask"}
        </button>
      </form>

      {error && <p className="error">{error}</p>}

      {answer && (
        <section className="answer-card">
          <h2>Answer</h2>
          <p className="answer-text">{answer}</p>

          {sources.length > 0 && (
            <div className="sources">
              <h3>Sources</h3>
              <ol className="source-list">
                {sources.map((s, i) => (
                  <li key={i} className="source-item">
                    <span className="source-tag">
                      page {s.page} · match {s.similarity}
                    </span>
                    <span className="source-excerpt">{s.excerpt}</span>
                  </li>
                ))}
              </ol>
            </div>
          )}
        </section>
      )}
    </main>
  );
}