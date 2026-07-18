import { api } from "./client";

export interface CreateInterviewRequest {
  resume_id?: number;
  job_id?: number;
  record_text: string;
}

export interface InterviewEvalResult {
  interview_id: number;
  summary: string;
  capability_eval: Record<string, string>;
  recommendation: string;
  rationale: Record<string, unknown>;
}

export async function createInterview(req: CreateInterviewRequest): Promise<{ interview_id: number; status: string }> {
  const resp = await api.post("/interviews", req);
  return resp.data;
}

export async function evaluateInterview(interviewId: number): Promise<InterviewEvalResult> {
  const resp = await api.post<InterviewEvalResult>(`/interviews/${interviewId}/evaluate`);
  return resp.data;
}
