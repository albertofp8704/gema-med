"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { useAuth } from "@clerk/nextjs";
import MessageBubble from "./MessageBubble";
import { sendChat } from "@/lib/api";
import { Message } from "@/lib/types";

interface Props {
  activeTopic: string | null;
  activeStep: number | null;
  sessionId: string | null;
  onSessionId: (id: string) => void;
  onProgressRefresh: () => void;
}

const QUICK_ACTIONS = [
  ["🫀 Cardio Step 2",   "Dame una pregunta de cardiology del Step 2"],
  ["🧠 Neuro Step 1",    "Dame una pregunta de neurology del Step 1"],
  ["💊 Farmaco Step 1",  "Dame una pregunta de pharmacology del Step 1"],
  ["🔬 Micro aleatorio", "Dame una pregunta de microbiology"],
  ["🇨🇺 Ruta ECFMG",    "Explícame el proceso de ECFMG para graduados cubanos en detalle"],
  ["📊 Mi progreso",     "Muéstrame mi progreso detallado por tema y step"],
];

export default function ChatWindow({
  activeTopic,
  activeStep,
  sessionId,
  onSessionId,
  onProgressRefresh,
}: Props) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput]       = useState("");
  const [loading, setLoading]   = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const { getToken, userId } = useAuth();

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const buildMessage = useCallback(
    (text: string): string => {
      // Single letter answer → pass through
      if (/^[a-eA-E]$/.test(text.trim())) return text.trim().toUpperCase();
      // If no active filter, send as-is
      if (!activeTopic && !activeStep) return text;
      // If it looks like a "give me a question" request, append filters
      const lower = text.toLowerCase();
      const isAsk = ["dame", "otra", "siguiente", "question", "pregunta", "quiz", "give", "next"].some(
        (w) => lower.includes(w)
      );
      if (isAsk) {
        let msg = "Dame una pregunta";
        if (activeTopic) msg += ` de ${activeTopic}`;
        if (activeStep)  msg += ` del Step ${activeStep}`;
        return msg;
      }
      return text;
    },
    [activeTopic, activeStep]
  );

  const send = useCallback(
    async (rawText: string) => {
      const text = rawText.trim();
      if (!text || loading) return;

      const token = await getToken();
      const msgToSend = buildMessage(text);

      setMessages((prev) => [...prev, { role: "user", content: text }]);
      setInput("");
      if (textareaRef.current) {
        textareaRef.current.style.height = "auto";
      }
      setLoading(true);

      try {
        // Use Clerk userId as session prefix for web users
        const sid = sessionId || (userId ? `web_${userId}` : null);
        const data = await sendChat(msgToSend, sid, token);
        onSessionId(data.session_id);
        setMessages((prev) => [...prev, { role: "agent", content: data.response }]);
        onProgressRefresh();
      } catch (err) {
        setMessages((prev) => [
          ...prev,
          { role: "agent", content: `❌ Error conectando al servidor: ${err}. ¿Está corriendo FastAPI en el puerto 8000?` },
        ]);
      } finally {
        setLoading(false);
      }
    },
    [loading, sessionId, userId, getToken, buildMessage, onSessionId, onProgressRefresh]
  );

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send(input);
    }
  };

  const autoResize = () => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 128) + "px";
  };

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* Messages area */}
      <div className="flex-1 overflow-y-auto p-5 space-y-4 bg-slate-50">
        {messages.length === 0 && (
          <WelcomeCard onQuick={(msg) => send(msg)} />
        )}
        {messages.map((msg, i) => (
          <MessageBubble key={i} message={msg} />
        ))}
        {loading && <TypingIndicator />}
        <div ref={bottomRef} />
      </div>

      {/* Active filter bar */}
      {(activeTopic || activeStep) && (
        <div className="px-5 py-2 bg-blue-50 border-t border-blue-100 text-xs text-blue-700 font-medium flex items-center gap-2">
          <span>🔍 Filtro activo:</span>
          {activeTopic && <span className="bg-blue-100 px-2 py-0.5 rounded-full">{activeTopic}</span>}
          {activeStep && <span className="bg-blue-100 px-2 py-0.5 rounded-full">Step {activeStep}</span>}
        </div>
      )}

      {/* Input bar */}
      <div className="bg-white border-t border-slate-200 px-4 py-3 flex gap-3 items-end">
        <textarea
          ref={textareaRef}
          rows={1}
          value={input}
          onChange={(e) => { setInput(e.target.value); autoResize(); }}
          onKeyDown={handleKeyDown}
          placeholder="Escribe tu respuesta (A/B/C/D/E) o pregunta..."
          className="flex-1 border border-slate-300 rounded-xl px-4 py-2.5 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent leading-relaxed"
          style={{ maxHeight: 128 }}
          disabled={loading}
        />
        <button
          onClick={() => send(input)}
          disabled={loading || !input.trim()}
          className="bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white font-semibold text-sm px-5 py-2.5 rounded-xl transition-colors whitespace-nowrap flex-shrink-0"
        >
          {loading ? "⏳" : "Enviar ↵"}
        </button>
      </div>
    </div>
  );
}

function TypingIndicator() {
  return (
    <div className="flex items-end gap-2">
      <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center text-sm flex-shrink-0">
        🩺
      </div>
      <div className="bg-white rounded-2xl rounded-bl-sm px-4 py-3 shadow-sm">
        <div className="flex gap-1.5">
          <span className="w-2 h-2 bg-slate-300 rounded-full dot-1" />
          <span className="w-2 h-2 bg-slate-300 rounded-full dot-2" />
          <span className="w-2 h-2 bg-slate-300 rounded-full dot-3" />
        </div>
      </div>
    </div>
  );
}

function WelcomeCard({ onQuick }: { onQuick: (t: string) => void }) {
  return (
    <div className="flex flex-col items-center justify-center py-12 px-4 text-center">
      <div className="text-5xl mb-4">🩺</div>
      <h2 className="text-2xl font-bold text-slate-800 mb-2">
        Bienvenido a GEMA-MED
      </h2>
      <p className="text-slate-500 text-sm mb-8 max-w-md">
        Tutor IA para USMLE Step 1 / 2 CK / 3 y reválida de título médico.
        Usa los filtros de la barra lateral o empieza con una acción rápida.
      </p>
      <div className="flex flex-wrap gap-2 justify-center max-w-lg">
        {QUICK_ACTIONS.map(([label, msg]) => (
          <button
            key={label}
            onClick={() => onQuick(msg)}
            className="bg-white hover:bg-blue-600 hover:text-white text-blue-700 border border-blue-200 hover:border-blue-600 rounded-xl px-3.5 py-2 text-sm font-medium transition-all shadow-sm"
          >
            {label}
          </button>
        ))}
      </div>
    </div>
  );
}
