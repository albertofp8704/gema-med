"use client";

import { useState, useCallback, useEffect } from "react";
import { useAuth } from "@clerk/nextjs";
import TopicSidebar from "@/components/TopicSidebar";
import ChatWindow from "@/components/ChatWindow";
import { fetchProgress, resetSession } from "@/lib/api";
import { ProgressData } from "@/lib/types";

export default function StudyPage() {
  const [activeTopic, setActiveTopic] = useState<string | null>(null);
  const [activeStep,  setActiveStep]  = useState<number | null>(null);
  const [sessionId,   setSessionId]   = useState<string | null>(null);
  const [progress,    setProgress]    = useState<ProgressData | null>(null);
  const { getToken, userId } = useAuth();

  const refreshProgress = useCallback(async () => {
    const uid = sessionId || (userId ? `web_${userId}` : null);
    if (!uid) return;
    try {
      const token = await getToken();
      const data  = await fetchProgress(uid, token);
      setProgress(data);
    } catch (_) {}
  }, [sessionId, userId, getToken]);

  useEffect(() => {
    refreshProgress();
  }, [refreshProgress]);

  const handleReset = async () => {
    if (!confirm("¿Reiniciar sesión? El historial de chat se borrará (el progreso en DB se mantiene).")) return;
    if (sessionId) {
      const token = await getToken();
      await resetSession(sessionId, token).catch(() => {});
    }
    setSessionId(null);
    // Reload to clear ChatWindow state (simplest approach)
    window.location.reload();
  };

  return (
    <div className="flex h-screen overflow-hidden bg-slate-50">
      <TopicSidebar
        activeTopic={activeTopic}
        activeStep={activeStep}
        progress={progress}
        onTopic={setActiveTopic}
        onStep={setActiveStep}
        onReset={handleReset}
      />

      <main className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <div className="bg-white border-b border-slate-200 px-6 py-3 flex items-center justify-between flex-shrink-0">
          <div>
            <h1 className="text-sm font-semibold text-slate-800">
              Tutor USMLE — ECFMG / Reválida
            </h1>
            <p className="text-xs text-slate-400 mt-0.5">
              {activeTopic || activeStep
                ? `Filtro: ${[activeTopic, activeStep ? `Step ${activeStep}` : ""].filter(Boolean).join(" · ")}`
                : "Preguntas mixtas — sin filtro activo"}
            </p>
          </div>
          <div className="flex items-center gap-3">
            {progress && progress.total_answered > 0 && (
              <span className="text-xs font-semibold text-slate-500 bg-slate-100 px-2.5 py-1 rounded-full">
                {progress.overall_accuracy}% precisión · {progress.total_answered} preguntas
              </span>
            )}
          </div>
        </div>

        <ChatWindow
          activeTopic={activeTopic}
          activeStep={activeStep}
          sessionId={sessionId}
          onSessionId={setSessionId}
          onProgressRefresh={refreshProgress}
        />
      </main>
    </div>
  );
}
