"use client";
import { useEffect, useState } from "react";
import "./globals.css";

const KEY = "studio-meta-api-key";

async function call(path, key, body, isForm) {
  const res = await fetch(path, {
    method: "POST",
    headers: { "x-meta-api-key": key },
    body: isForm ? body : JSON.stringify(body),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || `Request failed (${res.status})`);
  return data;
}

function useApiKey() {
  const [apiKey, setApiKey] = useState("");
  useEffect(() => setApiKey(localStorage.getItem(KEY) || ""), []);
  const save = (v) => {
    setApiKey(v);
    localStorage.setItem(KEY, v);
  };
  return [apiKey, save];
}

export default function Home() {
  const [apiKey, setApiKey] = useApiKey();
  const [topic, setTopic] = useState("");
  const [busy, setBusy] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [chat, setChat] = useState([]);
  const [chatInput, setChatInput] = useState("");
  const [chatPrev, setChatPrev] = useState(null);
  const [budgetText, setBudgetText] = useState("");

  const run = async (name, path, body, isForm) => {
    setBusy(name); setError(""); setResult(null);
    try {
      setResult({ name, data: await call(path, apiKey, body, isForm) });
    } catch (e) { setError(e.message); }
    setBusy(null);
  };

  const sendChat = async () => {
    if (!chatInput.trim() || busy) return;
    const prompt = chatInput; setChatInput("");
    setChat((c) => [...c, { who: "you", text: prompt }]);
    setBusy("chat"); setError("");
    try {
      const d = await call("/api/chat", apiKey, { prompt, previousResponseId: chatPrev });
      setChatPrev(d.responseId);
      setChat((c) => [...c, { who: "studio", text: d.text }]);
    } catch (e) { setError(e.message); }
    setBusy(null);
  };

  const upload = async (name, path, field, file) => {
    if (!file) return;
    const form = new FormData();
    form.append(field, file);
    run(name, path, form, true);
  };

  const renderResult = () => {
    if (!result) return null;
    const { name, data } = result;
    return (
      <div className="card">
        <h2>{name}</h2>
        {name === "Cover art" && data.image && <img className="cover" src={data.image} alt="generated cover" />}
        {name === "Article" && data.article && (
          <div>
            <h3>{data.article.title}</h3><p><i>{data.article.subtitle}</i></p>
            {data.article.sections.map((s, i) => (<div key={i}><h4>{s.heading}</h4><p>{s.body}</p></div>))}
            <p><b>Takeaways:</b> {data.article.takeaways.join(" · ")}</p>
            <p className="small">Tags: {data.article.tags.join(", ")}</p>
          </div>
        )}
        {name === "Reading time" && data.answer && (
          <div>
            <pre>{data.toolCalls.map((t) => `tool: ${t.name}(${JSON.stringify(t.args)}) → ${t.minutes} min`).join("\n")}</pre>
            <p>{data.answer}</p>
          </div>
        )}
        {name === "Token budget" && <p>{data.tokens.toLocaleString()} input tokens ≈ ${data.usd.toFixed(4)}</p>}
        {(name === "Research brief" || name === "Cover critique") && <pre>{data.text}</pre>}
        {name === "Transcript" && <pre>{data.transcript}</pre>}
      </div>
    );
  };

  return (
    <main>
      <h1>Content Studio</h1>
      <p className="sub">Research, write, illustrate, and narrate — powered by the Meta Model API.</p>

      <div className="card">
        <h2>API key</h2>
        <div className="row">
          <input type="password" placeholder="Paste your Meta Model API key" value={apiKey} onChange={(e) => setApiKey(e.target.value)} />
        </div>
        <p className="small">Stored only in this browser (localStorage). Never sent anywhere except api.meta.ai.</p>
      </div>

      <div className="card">
        <h2>Create from a topic</h2>
        <div className="row">
          <input type="text" placeholder="e.g. Meta AI glasses" value={topic} onChange={(e) => setTopic(e.target.value)} />
        </div>
        <div className="row" style={{ marginTop: 10 }}>
          <button disabled={busy || !topic} onClick={() => run("Research brief", "/api/research", { topic })}>Research {busy === "Research brief" && "…"}</button>
          <button disabled={busy || !topic} onClick={() => run("Article", "/api/article", { topic })}>Article {busy === "Article" && "…"}</button>
          <button disabled={busy || !topic} onClick={() => run("Cover art", "/api/cover", { topic })}>Cover art ($0.01) {busy === "Cover art" && "…"}</button>
          <button disabled={busy || !topic} onClick={() => run("Reading time", "/api/tools", { topic, words: 1850 })}>Reading time {busy === "Reading time" && "…"}</button>
        </div>
      </div>

      <div className="card">
        <h2>Refine with chat</h2>
        <div className="chatlog">
          {chat.map((m, i) => <div key={i} className={`msg ${m.who}`}>{m.text}</div>)}
        </div>
        <div className="row">
          <input type="text" placeholder="Ask to refine the piece…" value={chatInput} onChange={(e) => setChatInput(e.target.value)} onKeyDown={(e) => e.key === "Enter" && sendChat()} />
          <button disabled={busy} onClick={sendChat}>Send {busy === "chat" && "…"}</button>
        </div>
        <p className="small">Reasoning carries across turns via response chaining.</p>
      </div>

      <div className="card">
        <h2>Cover critique</h2>
        <div className="row">
          <input type="file" accept="image/*" onChange={(e) => upload("Cover critique", "/api/describe", "image", e.target.files[0])} />
        </div>
      </div>

      <div className="card">
        <h2>Transcribe voiceover</h2>
        <div className="row">
          <input type="file" accept="audio/*" onChange={(e) => upload("Transcript", "/api/narrate", "audio", e.target.files[0])} />
        </div>
        <p className="small">WAV audio works best (the transcription API takes WAV only).</p>
      </div>

      <div className="card">
        <h2>Token budget</h2>
        <textarea placeholder="Paste text to count tokens…" value={budgetText} onChange={(e) => setBudgetText(e.target.value)} />
        <div className="row" style={{ marginTop: 8 }}>
          <button disabled={busy || !budgetText} onClick={() => run("Token budget", "/api/budget", { text: budgetText })}>Count {busy === "Token budget" && "…"}</button>
        </div>
      </div>

      {error && <p className="err">{error}</p>}
      {renderResult()}
    </main>
  );
}
