import { useState } from "react";
import { Card, Button, Input, Form, Descriptions, Tag, Space, Typography, message } from "antd";
import { createInterview, evaluateInterview, InterviewEvalResult } from "../api/interview";

const { TextArea } = Input;
const { Title } = Typography;

const REC_COLORS: Record<string, string> = { "推荐": "green", "待定": "orange", "不推荐": "red" };

export default function InterviewPage() {
  const [loading, setLoading] = useState(false);
  const [interviewId, setInterviewId] = useState<number | null>(null);
  const [result, setResult] = useState<InterviewEvalResult | null>(null);

  const onCreate = async (values: { record_text: string; resume_id?: string; job_id?: string }) => {
    setLoading(true);
    setResult(null);
    try {
      const data = await createInterview({
        record_text: values.record_text,
        resume_id: values.resume_id ? Number(values.resume_id) : undefined,
        job_id: values.job_id ? Number(values.job_id) : undefined,
      });
      setInterviewId(data.interview_id);
      message.success("面试记录已保存");

      // 自动触发评价
      const evalData = await evaluateInterview(data.interview_id);
      setResult(evalData);
      message.success("面试评价已完成");
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    } catch (err: any) {
      message.error(err?.message || "操作失败");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <Title level={3}>AI 面试助手</Title>
      <Card style={{ marginBottom: 16 }}>
        <Form onFinish={onCreate} initialValues={{ record_text: "" }}>
          <Form.Item name="resume_id" label="简历 ID">
            <Input placeholder="选填" style={{ width: 120 }} />
          </Form.Item>
          <Form.Item name="job_id" label="岗位 ID">
            <Input placeholder="选填" style={{ width: 120 }} />
          </Form.Item>
          <Form.Item name="record_text" label="面试记录" rules={[{ required: true, message: "请输入面试记录" }]}>
            <TextArea rows={6} placeholder="输入面试过程中的问答记录、行为观察等" />
          </Form.Item>
          <Button type="primary" htmlType="submit" loading={loading}>
            提交并评价
          </Button>
        </Form>
      </Card>

      {result && (
        <Card title={`面试评价（#${interviewId}）`}>
          <Descriptions column={1} bordered size="small">
            <Descriptions.Item label="总结">{result.summary}</Descriptions.Item>
            <Descriptions.Item label="推荐建议">
              <Tag color={REC_COLORS[result.recommendation] || "default"}>{result.recommendation}</Tag>
            </Descriptions.Item>
            <Descriptions.Item label="能力评价">
              <Space direction="vertical">
                {Object.entries(result.capability_eval || {}).map(([dim, val]) => (
                  <Tag key={dim}>{dim}：{String(val)}</Tag>
                ))}
              </Space>
            </Descriptions.Item>
            <Descriptions.Item label="评价依据">{JSON.stringify(result.rationale)}</Descriptions.Item>
          </Descriptions>
        </Card>
      )}
    </div>
  );
}
