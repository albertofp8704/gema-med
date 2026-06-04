export interface Message {
  role: "user" | "agent";
  content: string;
}

export interface ChatResponse {
  session_id: string;
  response: string;
  messages_in_session: number;
}

export interface TopicStat {
  topic: string;
  total: number;
  correct: number;
  accuracy: number;
}

export interface StepStat {
  step: number;
  total: number;
  correct: number;
  accuracy: number;
}

export interface ProgressData {
  user_id: string;
  total_answered: number;
  total_correct: number;
  overall_accuracy: number;
  by_topic: TopicStat[];
  by_step: StepStat[];
}

export interface Topic {
  emoji: string;
  label: string;
  code: string;
}

export const TOPICS: Topic[] = [
  { emoji: "🫀", label: "Cardiology",       code: "cardiology" },
  { emoji: "🫁", label: "Pulmonology",      code: "pulmonology" },
  { emoji: "🧠", label: "Neurology",        code: "neurology" },
  { emoji: "🩸", label: "Hematology",       code: "hematology" },
  { emoji: "💊", label: "Pharmacology",     code: "pharmacology" },
  { emoji: "🔬", label: "Microbiology",     code: "microbiology" },
  { emoji: "🏥", label: "Gastroenterology", code: "gastroenterology" },
  { emoji: "⚕️",  label: "Nephrology",       code: "nephrology" },
  { emoji: "🧬", label: "Endocrinology",    code: "endocrinology" },
  { emoji: "🔭", label: "Pathology",        code: "pathology" },
  { emoji: "🤰", label: "OB/GYN",           code: "ob_gyn" },
  { emoji: "👶", label: "Pediatrics",       code: "pediatrics" },
  { emoji: "🧘", label: "Psychiatry",       code: "psychiatry" },
  { emoji: "📊", label: "Biostatistics",    code: "biostatistics" },
];
