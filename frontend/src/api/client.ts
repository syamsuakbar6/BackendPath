import type {
  AuthResponse,
  Dashboard,
  Language,
  LessonDetail,
  LessonProgress,
  ModuleMap,
  QuestionAnswerResponse,
  ReviewItem,
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
    throw new Error(error.detail ?? "Request failed");
  }
  return response.json() as Promise<T>;
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
  }
};
