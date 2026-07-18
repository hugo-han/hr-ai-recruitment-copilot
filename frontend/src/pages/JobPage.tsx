import { useState } from "react";
import { Form, Input, Button, Card, Typography, Descriptions, Tag, Divider, Space, message } from "antd";
import { draftJob, DraftJobResult, getJob, updateJob, listVersions } from "../api/job";

const { Title, Paragraph, Text } = Typography;
const { TextArea } = Input;

export default function JobPage() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<DraftJobResult | null>(null);
  const [versions, setVersions] = useState<Record<string, unknown>[]>([]);
  const [editing, setEditing] = useState(false);

  const onDraft = async (values: { title: string; level: string; business_req: string }) => {
    setLoading(true);
    setResult(null);
    try {
      const data = await draftJob(values);
      setResult(data);
      message.success("JD 生成成功");
      // 加载版本列表
      const vs = await listVersions(data.job_id);
      setVersions(vs);
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    } catch (err: any) {
      message.error(err?.message || "JD 生成失败");
    } finally {
      setLoading(false);
    }
  };

  const onSaveEdit = async (values: Record<string, unknown>) => {
    if (!result) return;
    setLoading(true);
    try {
      await updateJob(result.job_id, { jd: values });
      message.success("已保存新版本");
      setEditing(false);
      const job = await getJob(result.job_id);
      setResult({ ...result, jd: job.job_profile ? { ...result.jd, ...job.job_profile } : result.jd });
      const vs = await listVersions(result.job_id);
      setVersions(vs);
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    } catch (err: any) {
      message.error(err?.message || "保存失败");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <Title level={3}>AI 职位助手</Title>
      <Paragraph type="secondary">输入岗位信息，自动生成 JD、岗位画像与技能要求</Paragraph>

      <Card style={{ marginBottom: 16 }}>
        <Form onFinish={onDraft} layout="inline" style={{ flexWrap: "wrap", gap: 8 }}>
          <Form.Item name="title" rules={[{ required: true, message: "请输入岗位名称" }]}>
            <Input placeholder="岗位名称，如：Java工程师" style={{ width: 200 }} />
          </Form.Item>
          <Form.Item name="level" rules={[{ required: true, message: "请输入岗位等级" }]}>
            <Input placeholder="岗位等级，如：P5" style={{ width: 120 }} />
          </Form.Item>
          <Form.Item name="business_req">
            <TextArea placeholder="业务要求（选填）" style={{ width: 300 }} rows={1} />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading}>
              生成 JD
            </Button>
          </Form.Item>
        </Form>
      </Card>

      {result && (
        <Card
          title={`${result.jd?.title || ""} — JD 草稿（版本 ${result.version_no}）`}
          extra={
            <Space>
              <Button onClick={() => setEditing(!editing)}>{editing ? "取消编辑" : "编辑 JD"}</Button>
            </Space>
          }
        >
          {editing ? (
            <Form onFinish={onSaveEdit} initialValues={{ title: result.jd?.title, responsibilities: (result.jd?.responsibilities as string[])?.join("\n"), requirements: (result.jd?.requirements as string[])?.join("\n") }}>
              <Form.Item name="title" label="标题">
                <Input />
              </Form.Item>
              <Form.Item name="responsibilities" label="职责（每行一条）">
                <TextArea rows={4} />
              </Form.Item>
              <Form.Item name="requirements" label="要求（每行一条）">
                <TextArea rows={4} />
              </Form.Item>
              <Button type="primary" htmlType="submit" loading={loading}>保存为人工版本</Button>
            </Form>
          ) : (
            <>
              <Descriptions column={1} size="small">
                <Descriptions.Item label="职责">
                  {(result.jd?.responsibilities as string[])?.map((r: string, i: number) => <div key={i}>• {r}</div>)}
                </Descriptions.Item>
                <Descriptions.Item label="任职要求">
                  {(result.jd?.requirements as string[])?.map((r: string, i: number) => <div key={i}>• {r}</div>)}
                </Descriptions.Item>
              </Descriptions>
              <Divider />
              <Title level={5}>岗位画像</Title>
              <Descriptions column={2} size="small">
                {Object.entries(result.job_profile || {}).map(([k, v]) => (
                  <Descriptions.Item key={k} label={k}>{String(v)}</Descriptions.Item>
                ))}
              </Descriptions>
              <Divider />
              <Title level={5}>技能要求</Title>
              <Space wrap>
                {(result.skill_requirements || []).map((s: string) => <Tag key={s} color="blue">{s}</Tag>)}
              </Space>
              <Divider />
              <Text type="secondary">生成依据：{result.rationale}</Text>
              <Divider />
              <Title level={5}>版本历史</Title>
              {versions.map((v) => (
                <Tag key={v.version_no as number} color={v.source === "AI" ? "green" : "orange"}>
                  v{v.version_no as number} ({v.source})
                </Tag>
              ))}
            </>
          )}
        </Card>
      )}
    </div>
  );
}
