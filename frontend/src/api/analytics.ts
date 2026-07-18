import { api } from "./client";

export interface AnalyticsOverview {
  recruitment_cycle_days: number | null;
  conversion_rate: Record<string, number>;
  channel_effectiveness: Record<string, { uploaded: number; recommended: number; recommended_rate: number }>;
  total_jobs: number;
  total_resumes: number;
  total_interviews: number;
}

export async function getOverview(start?: string, end?: string): Promise<AnalyticsOverview> {
  const resp = await api.get<AnalyticsOverview>("/analytics/overview", { params: { start, end } });
  return resp.data;
}
