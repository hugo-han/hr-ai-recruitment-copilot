import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Form, Input, Button, Card, Typography, message } from "antd";
import { UserOutlined, LockOutlined } from "@ant-design/icons";
import { login, getMe } from "../api/auth";
import { useAuthStore } from "../store/auth";

const { Title, Text } = Typography;

export default function LoginPage() {
  const [loading, setLoading] = useState(false);
  const { setAuth, token } = useAuthStore();
  const navigate = useNavigate();

  useEffect(() => {
    if (token) {
      getMe().catch(() => {
        // token 过期或无效，清空重登
      });
    }
  }, [token]);

  const onFinish = async (values: { username: string; password: string }) => {
    setLoading(true);
    try {
      const result = await login(values.username, values.password);
      setAuth(result.access_token, result.role, result.name);
      message.success(`欢迎回来，${result.name}`);
      navigate("/jobs", { replace: true });
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    } catch (err: any) {
      message.error(err?.response?.data?.message || err?.message || "登录失败");
    } finally {
      setLoading(false);
    }
  };

  // 如果已登录则跳过登录页
  useEffect(() => {
    if (token) navigate("/jobs", { replace: true });
  }, [token, navigate]);

  return (
    <div style={{ display: "flex", justifyContent: "center", alignItems: "center", minHeight: "100vh", background: "#f0f2f5" }}>
      <Card style={{ width: 400, boxShadow: "0 2px 8px rgba(0,0,0,0.15)" }}>
        <div style={{ textAlign: "center", marginBottom: 24 }}>
          <Title level={3}>HR 招聘 AI 助手</Title>
          <Text type="secondary">登录系统以使用 AI 招聘能力</Text>
        </div>
        <Form onFinish={onFinish} size="large">
          <Form.Item name="username" rules={[{ required: true, message: "请输入用户名" }]}>
            <Input prefix={<UserOutlined />} placeholder="用户名" />
          </Form.Item>
          <Form.Item name="password" rules={[{ required: true, message: "请输入密码" }]}>
            <Input.Password prefix={<LockOutlined />} placeholder="密码" />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading} block aria-label="登录">
              登录
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
}
