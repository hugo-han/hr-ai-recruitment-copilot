import { Card, Typography } from "antd";

const { Title, Paragraph } = Typography;

export default function DashboardPage() {
  return (
    <Card>
      <Title level={3}>欢迎来到 HR 招聘 AI 助手</Title>
      <Paragraph>项目脚手架已就绪。各 AI 助手模块将陆续上线：职位 / 简历 / 面试 / 数据分析。</Paragraph>
    </Card>
  );
}
