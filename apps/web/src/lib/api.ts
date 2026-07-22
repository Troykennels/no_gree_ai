import type {
  AuthUser,
  AutomationState,
  Channel,
  DailyReport,
  EngineStatus,
  IntelligenceResult,
  Scan,
  ScanList,
  ScamResult,
  TokenResponse,
  TransactionResult,
} from "./types";

const BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
const API = `${BASE_URL}/api/v1`;

/** Absolute URL of the Automation Engine SSE stream (for EventSource). */
export const automationStreamUrl = () => `${API}/automation/stream`;

const TOKEN_KEY = "securenaija.access_token";

export const tokenStore = {
  get(): string | null {
    if (typeof window === "undefined") return null;
    return window.localStorage.getItem(TOKEN_KEY);
  },
  set(token: string) {
    window.localStorage.setItem(TOKEN_KEY, token);
  },
  clear() {
    window.localStorage.removeItem(TOKEN_KEY);
  },
};

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(
  path: string,
  options: RequestInit = {},
  auth = false,
): Promise<T> {
  const headers = new Headers(options.headers);
  headers.set("Content-Type", "application/json");
  if (auth) {
    const token = tokenStore.get();
    if (token) headers.set("Authorization", `Bearer ${token}`);
  }

  const res = await fetch(`${API}${path}`, { ...options, headers });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail ?? detail;
    } catch {
      /* non-JSON error body */
    }
    throw new ApiError(res.status, detail);
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export const api = {
  health: () =>
    request<{ status: string; model_ready: boolean; model_version: string }>(
      "/health",
    ),

  detect: (message: string, channel: Channel = "other") =>
    request<Scan>(
      "/fraud/detect",
      { method: "POST", body: JSON.stringify({ message, channel }) },
      true, // sends token if present so authed scans are saved
    ),

  // Model 1 — Scam Detection (Safe / Suspicious / Scam + highlighted words)
  detectScam: (message: string) =>
    request<ScamResult>("/scam/detect", {
      method: "POST",
      body: JSON.stringify({ message }),
    }),

  // Model 2 — Transaction Fraud (send whatever fields you have; rest imputed)
  scoreTransaction: (features: Record<string, number | string | null>) =>
    request<TransactionResult>("/transaction/score", {
      method: "POST",
      body: JSON.stringify({ features }),
    }),

  // Fraud Intelligence — fuse both models into one 0-100 score + AI actions
  assessIntelligence: (
    message: string | null,
    transactionFeatures?: Record<string, number | string | null> | null,
    channel: Channel = "sms",
  ) =>
    request<IntelligenceResult>("/intelligence/assess", {
      method: "POST",
      body: JSON.stringify({
        message: message || null,
        channel,
        transaction: transactionFeatures ? { features: transactionFeatures } : null,
      }),
    }),

  engineStatus: () => request<EngineStatus>("/engine/status"),

  // ── Automation Engine ──────────────────────────────────────────────────────
  automationSnapshot: () => request<AutomationState>("/automation/snapshot"),

  ingestMessage: (message: string, channel: Channel = "sms", region?: string) =>
    request<Record<string, unknown>>("/automation/ingest/message", {
      method: "POST",
      body: JSON.stringify({ message, channel, region }),
    }),

  ingestTransaction: (
    features: Record<string, number | string | null>,
    region?: string,
  ) =>
    request<Record<string, unknown>>("/automation/ingest/transaction", {
      method: "POST",
      body: JSON.stringify({ features, region }),
    }),

  simulate: (count = 40, interval_ms = 900) =>
    request<{ started: boolean; running: boolean }>("/automation/simulate", {
      method: "POST",
      body: JSON.stringify({ count, interval_ms }),
    }),

  simulateStop: () =>
    request<{ running: boolean }>("/automation/simulate/stop", { method: "POST" }),

  sendFeedback: (item_id: string, label: "Safe" | "Scam") =>
    request<{ item_id: string; label: string; feedback_count: number }>(
      "/automation/feedback",
      { method: "POST", body: JSON.stringify({ item_id, label }) },
    ),

  dailyReport: () => request<DailyReport>("/automation/report/daily"),

  register: (email: string, full_name: string, password: string) =>
    request<AuthUser>("/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, full_name, password }),
    }),

  login: async (email: string, password: string) => {
    const tokens = await request<TokenResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    tokenStore.set(tokens.access_token);
    return tokens;
  },

  me: () => request<AuthUser>("/auth/me", {}, true),

  scans: (limit = 20, offset = 0) =>
    request<ScanList>(`/fraud/scans?limit=${limit}&offset=${offset}`, {}, true),
};
