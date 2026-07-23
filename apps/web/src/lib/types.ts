// Mirror of the API contract (apps/api/app/interface/schemas.py).

export type Channel = "sms" | "whatsapp" | "email" | "pos" | "other";

export type RiskBand = "critical" | "high" | "elevated" | "low" | "minimal";

export interface RiskFactor {
  label: string;
  signal: "fraud" | "safe";
  weight: number;
}

export interface Assessment {
  fraud_probability: number;
  is_fraud: boolean;
  risk_band: RiskBand;
  risk_label: string;
  verdict: string;
  factors: RiskFactor[];
  model_version: string;
}

export interface Scan {
  id: string;
  message: string;
  channel: Channel;
  assessment: Assessment;
  created_at?: string | null;
}

export interface ScanList {
  items: Scan[];
  total: number;
  limit: number;
  offset: number;
}

// ── Model 1: Scam Detection ──────────────────────────────────────────────────

export type ScamLabel = "Safe" | "Suspicious" | "Scam";

export interface ScamWord {
  word: string;
  weight: number;
}

export interface ScamResult {
  label: ScamLabel;
  scam_probability: number;
  confidence: number;
  highlighted_words: ScamWord[];
  explanation: string;
  model_version: string;
}

// ── Model 2: Transaction Fraud ───────────────────────────────────────────────

export type TxnDecision = "approve" | "review" | "decline";

export interface TxnFactor {
  feature: string;
  label: string;
  signal: "fraud" | "safe";
  weight: number;
}

export interface TransactionResult {
  fraud_probability: number;
  confidence: number;
  is_fraud: boolean;
  decision: TxnDecision;
  risk_band: RiskBand;
  reasons: string[];
  verdict: string;
  risk_explanation: string;
  factors: TxnFactor[];
  model_version: string;
  algorithm: string;
}

// ── Engine status ────────────────────────────────────────────────────────────

export interface EngineModelStatus {
  key: string;
  name: string;
  ready: boolean;
  version: string;
  error?: string | null;
}

export interface EngineStatus {
  status: string;
  models: EngineModelStatus[];
}

// ── Fraud Intelligence Engine ────────────────────────────────────────────────

export type RiskCategory = "Safe" | "Low" | "Medium" | "High" | "Critical";
export type Priority = "critical" | "high" | "medium" | "low" | "info";

export interface IntelSignal {
  type: string;
  label: string;
  severity: Priority;
}

export interface IntelRecommendation {
  id: string;
  action: string;
  detail: string;
  priority: Priority;
}

export interface IntelScamComponent {
  label: ScamLabel;
  probability: number;
  confidence: number;
  highlighted_words: ScamWord[];
  explanation: string;
}

export interface IntelTxnComponent {
  decision: TxnDecision;
  probability: number;
  risk_band: RiskBand;
  verdict: string;
  factors: TxnFactor[];
}

export interface IntelligenceResult {
  overall_risk_score: number;
  category: RiskCategory;
  confidence: number;
  summary: string;
  human_explanation: string;
  risk_explanation: string;
  reasons: string[];
  scam: IntelScamComponent | null;
  transaction: IntelTxnComponent | null;
  signals: IntelSignal[];
  recommendations: IntelRecommendation[];
  model_versions: Record<string, string>;
  assessed_at: string;
}

// ── Automation Engine ────────────────────────────────────────────────────────

export interface AutomationStats {
  messages_scanned: number;
  transactions_analyzed: number;
  scams_detected: number;
  frauds_blocked: number;
  alerts: number;
  value_protected: number;
  feedback_count: number;
}

export interface TimelinePoint {
  t: string;
  threats: number;
  safe: number;
}

export type HeatLevel = "low" | "medium" | "high";

export interface HeatCell {
  region: string;
  total: number;
  threats: number;
  level: HeatLevel;
}

export type AlertSeverity = "critical" | "warning";

export interface EngineAlert {
  id: string;
  ref_id: string;
  kind: "message" | "transaction";
  severity: AlertSeverity;
  title: string;
  detail: string;
  probability: number;
  region: string;
  amount?: number | null;
  status: "new" | "reviewed";
  feedback?: string | null;
  ts: string;
}

export interface ActivityItem {
  id: string;
  kind: "message" | "transaction";
  label: string;
  probability: number;
  is_threat: boolean;
  region: string;
  ts: string;
}

export interface DailyReport {
  id: string;
  generated_at: string;
  period: string;
  security_score: number;
  security_grade: string;
  totals: AutomationStats;
  top_threat_regions: { region: string; threats: number; total: number }[];
  critical_alerts: number;
  headline: string;
}

export interface RecentMessage {
  id: string;
  channel: string;
  text: string;
  label: ScamLabel;
  probability: number;
  region: string;
  is_threat: boolean;
  ts: string;
}

export interface RecentTransaction {
  id: string;
  amount: number;
  bank?: string | null;
  payer?: string | null;
  decision: TxnDecision;
  probability: number;
  risk_band: RiskBand;
  region: string;
  is_threat: boolean;
  ts: string;
}

export interface Analytics {
  messages: { Scam: number; Suspicious: number; Safe: number };
  transactions: { decline: number; review: number; approve: number };
}

export interface AutomationState {
  stats: AutomationStats;
  security_score: number;
  security_grade: string;
  risk_score: number;
  timeline: TimelinePoint[];
  heatmap: HeatCell[];
  alerts: EngineAlert[];
  activity: ActivityItem[];
  recent_messages: RecentMessage[];
  recent_transactions: RecentTransaction[];
  analytics: Analytics;
  report: DailyReport | null;
  live_subscribers: number;
  uptime_seconds: number;
  updated_at: string;
}

export type NotificationPriority = "info" | "warning" | "danger" | "critical";

export interface NotificationPayload {
  priority: NotificationPriority;
  title: string;
  body: string;
}

export interface StreamNotification {
  type: "notification";
  item: ActivityItem & { text?: string; decision?: string; amount?: number };
  alert: EngineAlert | null;
  is_threat: boolean;
  notification?: NotificationPayload;
}

export type StreamEvent =
  | { type: "state"; state: AutomationState }
  | StreamNotification
  | { type: "security_score"; score: number; grade: string; delta: number }
  | { type: "report_ready"; report: DailyReport }
  | { type: "feedback_recorded"; item_id: string; label: string; feedback_count: number }
  | { type: "heartbeat" };

export interface AuthUser {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  role?: string;
  created_at?: string | null;
}

export interface AuditLogEntry {
  [key: string]: string;
  ts: string;
  event: string;
  actor: string;
  detail: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}
