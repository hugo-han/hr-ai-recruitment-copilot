import { api } from "./client";

export interface UploadResult {
  resume_id: number;
  file_ref: string;
  channel: string;
}

export interface AnalyzeResult {
  resume_id: number;
  job_id: number;
  match_score: number;
  advantages: string[];
  risks: string[];
  rationale: Record<string, unknown>;
}

export interface ResumeListItem {
  id: number;
  file_name: string;
  status: string;
  job_id: number | null;
  channel: string;
  match_score: number | null;
}

export async function uploadResume(file: File, jobId?: number, channel?: string): Promise<UploadResult> {
  const form = new FormData();
  form.append("file", file);
  if (jobId != null) form.append("job_id", String(jobId));
  if (channel) form.append("channel", channel);
  const resp = await api.post<UploadResult>("/resumes/upload", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return resp.data;
}

export async function analyzeResume(resumeId: number, jobId: number): Promise<AnalyzeResult> {
  const resp = await api.post<AnalyzeResult>(`/resumes/${resumeId}/analyze`, { job_id: jobId });
  return resp.data;
}

export async function listResumes(sort?: string): Promise<ResumeListItem[]> {
  const resp = await api.get<ResumeListItem[]>("/resumes", { params: { sort } });
  return resp.data;
}

export async function deleteResume(resumeId: number) {
  const resp = await api.delete(`/resumes/${resumeId}`);
  return resp.data;
}

export async function transitionStatus(resumeId: number, targetStatus: string) {
  const resp = await api.put(`/resumes/${resumeId}/status`, { target_status: targetStatus });
  return resp.data;
}

export async function exportResume(resumeId: number) {
  const resp = await api.get<{ content_b64: string; file_name: string; size: number }>(`/resumes/${resumeId}/export`);
  return resp.data;
}

export async function batchAnalyze(resumeIds: number[], jobId: number) {
  const resp = await api.post("/resumes/batch-analyze", { resume_ids: resumeIds, job_id: jobId });
  return resp.data;
}
