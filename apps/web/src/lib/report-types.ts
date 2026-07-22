// Mirrors ml/snaija_ml/data/preprocess.py report schema.

export interface DatasetStats {
  name: string;
  kind: "text" | "tabular";
  purpose: string;
  status?: "not_downloaded" | "error";
  note?: string;

  rows_raw?: number;
  rows_processed?: number;
  n_features?: number;

  missing_values?: number;
  missing_pct?: number;
  top_missing_columns?: Record<string, number>;
  high_missing_columns_dropped?: number;

  duplicates_removed?: number;
  outliers_removed?: number;
  outliers_clipped?: number;

  class_distribution?: Record<string, number>;
  class_balance_ratio?: number;
  positive_ratio?: number;
  fraud_ratio?: number;
  scam_ratio?: number;

  category_distribution?: Record<string, number>;
  avg_token_count?: number;
  imbalance_note?: string;
}

export interface DatasetReport {
  datasets: Record<string, DatasetStats>;
  generated_charts: string[];
  summary?: { total_datasets: number; total_rows: number };
}
