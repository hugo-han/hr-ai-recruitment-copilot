import { useEffect, useState } from "react";
import { Layout, Menu, Button, Typography, Spin, theme } from "antd";
import { Routes, Route, Navigate, useNavigate, useLocation } from "react-router-dom";
import { useAuthStore } from "./store/auth";
import { getMe } from "./api/auth";
import LoginPage from "./pages/LoginPage";
import JobPage from "./pages/JobPage";
import ResumePage from "./pages/ResumePage";
import InterviewPage from "./pages/InterviewPage";
import AnalyticsPage from "./pages/AnalyticsPage";

const { Header, Content, Sider } = Layout;

type MenuKey = "/jobs" | "/resumes" | "/interviews" | "/analytics";

const menuItems: { key: MenuKey; label: string }[] = [
  { key: "/jobs", label: "AI 职位助手" },
  { key: "/resumes", label: "AI 简历分析" },
  { key: "/interviews", label: "AI 面试助手" },
  { key: "/analytics", label: "数据分析" },
];

function ProtectedLayout() {
  const { token, role, name, setAuth, logout } = useAuthStore();
  const navigate = useNavigate();
  const location = useLocation();
  const [verifying, setVerifying] = useState(!name);

  const {
    token: { colorBgContainer },
  } = theme.useToken();

  useEffect(() => {
    if (token && !name) {
      getMe()
        .then((me) => setAuth(token, me.role, me.name))
        .catch(() => { logout(); navigate("/login", { replace: true }); })
        .finally(() => setVerifying(false));
    }
  }, [token, name, setAuth, logout, navigate]);

  if (!token) return <Navigate to="/login" replace />;
  if (verifying) return <Spin size="large" style={{ display: "block", margin: "200px auto" }} />;

  const selectedKey = (menuItems.find((m) => location.pathname.startsWith(m.key))?.key || "/jobs") as MenuKey;

  return (
    <Layout style={{ minHeight: "100vh" }}>
      <Sider collapsible>
        <div style={{ height: 48, color: "#fff", textAlign: "center", lineHeight: "48px", fontWeight: 600 }}>
          招聘 AI 助手
        </div>
        <Menu
          theme="dark"
          selectedKeys={[selectedKey]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
        />
      </Sider>
      <Layout>
        <Header
          style={{
            background: colorBgContainer,
            padding: "0 24px",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}
        >
          <Typography.Text strong>HR 招聘 AI 助手</Typography.Text>
          <div>
            <Typography.Text style={{ marginRight: 12 }}>
              {name}（{role}）
            </Typography.Text>
            <Button
              size="small"
              onClick={() => {
                logout();
                navigate("/login", { replace: true });
              }}
            >
              退出
            </Button>
          </div>
        </Header>
        <Content style={{ margin: "24px 16px", padding: 24, background: colorBgContainer, borderRadius: 8 }}>
          <Routes>
            <Route path="/" element={<Navigate to="/jobs" replace />} />
            <Route path="/jobs" element={<JobPage />} />
            <Route path="/resumes" element={<ResumePage />} />
            <Route path="/interviews" element={<InterviewPage />} />
            <Route path="/analytics" element={<AnalyticsPage />} />
            <Route path="*" element={<Navigate to="/jobs" replace />} />
          </Routes>
        </Content>
      </Layout>
    </Layout>
  );
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/*" element={<ProtectedLayout />} />
    </Routes>
  );
}
