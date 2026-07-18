import { useState, useEffect, useCallback } from "react";
import { Card, Typography, Upload, Button, Table, Tag, Space, Select, Dropdown, message } from "antd";
import { UploadOutlined, DownOutlined } from "@ant-design/icons";
import { uploadResume, analyzeResume, listResumes, deleteResume, exportResume, transitionStatus, AnalyzeResult, ResumeListItem } from "../api/resume";

const { Title, Text } = Typography;

// 状态机：允许的流转目标（对齐后端 ALLOWED_TRANSITIONS）
const ALLOWED_TRANSITIONS: Record<string, string[]> = {
  pending:   ["interview", "rejected"],
  interview: ["hired", "rejected"],
  hired:     [],
  rejected:  [],
};

const STATUS_LABELS: Record<string, { label: string; color: string }> = {
  pending:   { label: "待筛选", color: "default" },
  interview: { label: "面试", color: "blue" },
  hired:     { label: "录用", color: "green" },
  rejected:  { label: "淘汰", color: "red" },
  deleted:   { label: "已删除", color: "gray" },
};

export default function ResumePage() {
  const [resumes, setResumes] = useState<ResumeListItem[]>([]);
  const [analyzing, setAnalyzing] = useState<number | null>(null);
  const [analysis, setAnalysis] = useState<AnalyzeResult | null>(null);
  const [jobId, setJobId] = useState<number | undefined>();

  const refresh = useCallback(async () => {
    try {
      const data = await listResumes("score");
      setResumes(data);
    } catch { /* ignore */ }
  }, []);

  useEffect(() => { refresh(); }, [refresh]);

  const onUpload = async (info: { file: File }) => {
    try {
      await uploadResume(info.file, jobId);
      message.success("上传成功");
      refresh();
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    } catch (err: any) {
      message.error(err?.message || "上传失败");
    }
  };

  const onAnalyze = async (resumeId: number) => {
    if (!jobId) { message.warning("请先输入目标岗位 ID"); return; }
    setAnalyzing(resumeId);
    try {
      const data = await analyzeResume(resumeId, jobId);
      setAnalysis(data);
      message.success("评分完成");
      refresh();
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    } catch (err: any) {
      message.error(err?.message || "评分失败");
    } finally {
      setAnalyzing(null);
    }
  };

  const onDelete = async (resumeId: number) => {
    try {
      await deleteResume(resumeId);
      message.success("已删除");
      refresh();
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    } catch (err: any) {
      message.error(err?.message || "删除失败");
    }
  };

  const onExport = async (resumeId: number) => {
    try {
      const data = await exportResume(resumeId);
      const blob = new Blob([new Uint8Array(data.content_b64.match(/.{2}/g)!.map(b => parseInt(b, 16)))], { type: "application/octet-stream" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url; a.download = data.file_name; a.click();
      URL.revokeObjectURL(url);
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    } catch (err: any) {
      message.error(err?.message || "导出失败");
    }
  };

  const onTransition = async (resumeId: number, targetStatus: string) => {
    try {
      await transitionStatus(resumeId, targetStatus);
      message.success(`状态已更新为 ${STATUS_LABELS[targetStatus]?.label ?? targetStatus}`);
      refresh();
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    } catch (err: any) {
      message.error(err?.message || "状态流转失败");
    }
  };

  const columns = [
    { title: "ID", dataIndex: "id", width: 60 },
    { title: "文件名", dataIndex: "file_name" },
    {
      title: "状态", dataIndex: "status",
      render: (s: string) => {
        const meta = STATUS_LABELS[s] ?? { label: s, color: "default" };
        return <Tag color={meta.color}>{meta.label}</Tag>;
      },
    },
    { title: "渠道", dataIndex: "channel", render: (c: string) => <Tag color="geekblue">{c}</Tag> },
    { title: "匹配评分", dataIndex: "match_score", render: (s: number | null) => s != null ? <Tag color={s >= 70 ? "green" : s >= 40 ? "orange" : "red"}>{s}</Tag> : "-" },
    {
      title: "操作", render: (_: unknown, record: ResumeListItem) => {
        const targets = ALLOWED_TRANSITIONS[record.status] ?? [];
        return (
          <Space>
            <Button size="small" loading={analyzing === record.id} onClick={() => onAnalyze(record.id)}>评分</Button>
            {targets.length > 0 && (
              <Dropdown
                menu={{
                  items: targets.map((t) => ({
                    key: t,
                    label: STATUS_LABELS[t]?.label ?? t,
                    onClick: () => onTransition(record.id, t),
                  })),
                }}
              >
                <Button size="small">
                  推进状态 <DownOutlined />
                </Button>
              </Dropdown>
            )}
            <Button size="small" danger onClick={() => onDelete(record.id)}>删除</Button>
            <Button size="small" onClick={() => onExport(record.id)}>导出</Button>
          </Space>
        );
      },
    },
  ];

  return (
    <div>
      <Title level={3}>AI 简历分析助手</Title>
      <Card style={{ marginBottom: 16 }}>
        <Space>
          <span>目标岗位 ID：</span>
          <Select style={{ width: 120 }} placeholder="岗位ID" value={jobId} onChange={(v) => setJobId(v)}>
            <Select.Option value={1}>岗位 1</Select.Option>
            <Select.Option value={2}>岗位 2</Select.Option>
            <Select.Option value={3}>岗位 3</Select.Option>
          </Select>
          <Upload beforeUpload={() => false} onChange={(info) => onUpload({ file: info.file as unknown as File })} showUploadList={false}>
            <Button icon={<UploadOutlined />}>上传简历</Button>
          </Upload>
        </Space>
      </Card>

      {analysis && (
        <Card title="最近评分结果" style={{ marginBottom: 16 }}>
          <Space direction="vertical">
            <Text strong>匹配评分：</Text>
            <Tag color={analysis.match_score >= 70 ? "green" : analysis.match_score >= 40 ? "orange" : "red"}>
              {analysis.match_score}
            </Tag>
            <Text strong>优势：</Text>
            <ul>{analysis.advantages?.map((a, i) => <li key={i}>{a}</li>)}</ul>
            <Text strong>风险：</Text>
            <ul>{analysis.risks?.map((r, i) => <li key={i}>{r}</li>)}</ul>
            <Text type="secondary">依据：{JSON.stringify(analysis.rationale)}</Text>
          </Space>
        </Card>
      )}

      <Card title="简历列表">
        <Table rowKey="id" columns={columns} dataSource={resumes} pagination={false} size="small" />
      </Card>
    </div>
  );
}
