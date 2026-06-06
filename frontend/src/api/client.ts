import type {
  AuthResponse,
  AdminProofFilters,
  AdminProofOverrideRequest,
  AdminProofSubmission,
  Dashboard,
  Language,
  LessonDetail,
  LessonProgress,
  ModuleMap,
  ProofSubmission,
  ProofSubmissionRequest,
  ProofSubmissionResponse,
  QuestionAnswerResponse,
  ReviewItem,
  ReviewSubmissionRequest,
  ReviewSubmissionResponse,
  ProofEvaluationAnalytics,
  SearchResponse,
  Track,
  TrackDetail,
  User
} from "../types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";
const TOKEN_KEY = "backend_mastery_token";

export function getStoredToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function storeToken(token: string) {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getStoredToken();
  const headers = new Headers(options.headers);
  headers.set("Content-Type", "application/json");
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(formatError(error.detail ?? error));
  }
  return response.json() as Promise<T>;
}

function formatError(detail: unknown): string {
  if (typeof detail === "string") {
    return detail;
  }
  if (Array.isArray(detail)) {
    return detail
      .map((item) =>
        typeof item === "object" && item !== null && "msg" in item
          ? String(item.msg)
          : JSON.stringify(item)
      )
      .join("; ");
  }
  if (typeof detail === "object" && detail !== null) {
    const value = detail as { message?: unknown; errors?: unknown };
    const message = typeof value.message === "string" ? value.message : "Request failed";
    if (Array.isArray(value.errors)) {
      return `${message} ${value.errors.join(" ")}`;
    }
    return message;
  }
  return "Request failed";
}

export const api = {
  login(email: string, password: string) {
    return request<AuthResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password })
    });
  },
  register(full_name: string, email: string, password: string) {
    return request<AuthResponse>("/auth/register", {
      method: "POST",
      body: JSON.stringify({ full_name, email, password })
    });
  },
  me() {
    return request<User>("/auth/me");
  },
  languages() {
    return request<Language[]>("/languages");
  },
  tracks() {
    return request<Track[]>("/tracks");
  },
  track(id: number) {
    return request<TrackDetail>(`/tracks/${id}`);
  },
  module(id: number) {
    return request<ModuleMap>(`/modules/${id}`);
  },
  lesson(id: number) {
    return request<LessonDetail>(`/lessons/${id}`);
  },
  startLesson(id: number) {
    return request<{ progress: LessonProgress; message: string }>(`/lessons/${id}/start`, {
      method: "POST",
      body: JSON.stringify({})
    });
  },
  completeReading(id: number) {
    return request<{ progress: LessonProgress; message: string }>(
      `/lessons/${id}/complete-reading`,
      { method: "POST", body: JSON.stringify({}) }
    );
  },
  answerQuestion(id: number, answer: unknown) {
    return request<QuestionAnswerResponse>(`/questions/${id}/answer`, {
      method: "POST",
      body: JSON.stringify({ answer })
    });
  },
  submitExplainBack(id: number, answer: string) {
    return request<{ progress: LessonProgress; message: string }>(
      `/lessons/${id}/submit-explain-back`,
      { method: "POST", body: JSON.stringify({ answer }) }
    );
  },
  submitProof(id: number, payload: ProofSubmissionRequest) {
    return request<ProofSubmissionResponse>(`/lessons/${id}/proofs/submit`, {
      method: "POST",
      body: JSON.stringify(payload)
    });
  },
  lessonProofs(id: number) {
    return request<ProofSubmission[]>(`/lessons/${id}/proofs`);
  },
  completeDebugTask(id: number) {
    return request<{ progress: LessonProgress; message: string }>(
      `/lessons/${id}/complete-debug-task`,
      { method: "POST", body: JSON.stringify({}) }
    );
  },
  completeMiniTask(id: number) {
    return request<{ progress: LessonProgress; message: string }>(
      `/lessons/${id}/complete-mini-task`,
      { method: "POST", body: JSON.stringify({}) }
    );
  },
  submitReflection(id: number) {
    return request<{ progress: LessonProgress; message: string }>(
      `/lessons/${id}/submit-reflection`,
      { method: "POST", body: JSON.stringify({}) }
    );
  },
  dashboard() {
    return request<Dashboard>("/dashboard");
  },
  reviewsDue() {
    return request<ReviewItem[]>("/reviews/due");
  },
  submitReview(id: number, payload: ReviewSubmissionRequest) {
    return request<ReviewSubmissionResponse>(`/reviews/${id}/submit`, {
      method: "POST",
      body: JSON.stringify(payload)
    });
  },
  search(q: string) {
    return request<SearchResponse>(`/search?q=${encodeURIComponent(q)}`);
  },
  adminList(resource: string) {
    return request<unknown[]>(`/admin/${resource}`);
  },
  adminCreate(resource: string, payload: Record<string, unknown>) {
    return request<unknown>(`/admin/${resource}`, {
      method: "POST",
      body: JSON.stringify(payload)
    });
  },
  adminPublishLesson(id: number) {
    return request<unknown>(`/admin/lessons/${id}/publish`, {
      method: "POST",
      body: JSON.stringify({})
    });
  },
  adminArchiveLesson(id: number) {
    return request<unknown>(`/admin/lessons/${id}/archive`, {
      method: "POST",
      body: JSON.stringify({})
    });
  },
  adminPreviewLesson(id: number) {
    return request<LessonDetail>(`/admin/lessons/${id}/preview`);
  },
  adminExportLesson(id: number) {
    return request<Record<string, unknown>>(`/admin/content/export/lesson/${id}`);
  },
  adminImportLesson(payload: Record<string, unknown>) {
    return request<LessonDetail>("/admin/content/import/lesson", {
      method: "POST",
      body: JSON.stringify(payload)
    });
  },
  adminProofSubmissions(filters: AdminProofFilters = {}) {
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([key, value]) => {
      if (value) params.set(key, String(value));
    });
    const query = params.toString();
    return request<AdminProofSubmission[]>(`/admin/proof-submissions${query ? `?${query}` : ""}`);
  },
  adminProofSubmission(id: number) {
    return request<AdminProofSubmission>(`/admin/proof-submissions/${id}`);
  },
  adminOverrideProofSubmission(id: number, payload: AdminProofOverrideRequest) {
    return request<AdminProofSubmission>(`/admin/proof-submissions/${id}/override`, {
      method: "PATCH",
      body: JSON.stringify({
        ...payload,
        score_label: payload.score_label || null
      })
    });
  },
  adminProofEvaluationAnalytics() {
    return request<ProofEvaluationAnalytics>("/admin/proof-evaluation-analytics");
  }
};
