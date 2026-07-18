import { api } from "./client";

export interface DraftJobRequest {
  title: string;
  level: string;
  business_req: string;
}

export interface DraftJobResult {
  job_id: number;
  version_no: number;
  jd: Record<string, unknown>;
  job_profile: Record<string, unknown>;
  skill_requirements: string[];
  rationale: string;
}

export async function draftJob(req: DraftJobRequest): Promise<DraftJobResult> {
  const resp = await api.post<DraftJobResult>("/jobs/draft", req);
  return resp.data;
}

export async function getJob(jobId: number) {
  const resp = await api.get(`/jobs/${jobId}`);
  return resp.data;
}

export async function updateJob(jobId: number, data: Record<string, unknown>) {
  const resp = await api.put(`/jobs/${jobId}`, data);
  return resp.data;
}

export async function listVersions(jobId: number) {
  const resp = await api.get(`/jobs/${jobId}/versions`);
  return resp.data;
}
