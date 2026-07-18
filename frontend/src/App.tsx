import { useEffect, useState } from "react";
import { Layout, Menu, Button, Typography, Spin, Result, theme } from "antd";
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

// 角色 → 可见菜单（对齐后端 ROLE_PERMISSIONS）。Fix: Issue #4
const ROLE_MENUS: Record<string, MenuKey[]> = {
  HR:          ["/jobs", "/resumes", "/interviews"],
  HR_LEAD:     ["/jobs", "/resumes", "/interviews", "/analytics"],
  INTERVIEWER: ["/interviews"],
  ADMIN:       ["/jobs", "/resumes", "/interviews", "/analytics"],
};

const ALL_MENU_ITEMS: { key: MenuKey; label: string }[] = [
  { key: "/jobs",       label: "AI 职位助手" },
  { key: "/resumes",    label: "AI 简历分析" },
  { key: "/interviews", label: "AI 面试助手" },
  { key: "/analytics",  label: "数据分析" },
];

export function getVisibleMenus(role: string): { key: MenuKey; label: string }[] {
  const allowed = ROLE_MENUS[role] ?? ["/jobs", "/resumes", "/interviews"];
  return ALL_MENU_ITEMS.filter((m) => allowed.includes(m.key));
}

function RequirePermission({ role, path, children }: { role: string; path: MenuKey; children: JSX.Element }) {
  const allowed = ROLE_MENUS[role] ?? ["/jobs", "/resumes", "/interviews"];
  if (!allowed.includes(path)) {
    return (
      <Result
        status="403"
        title="403"
        subTitle="您的角色无权访问此功能"
      />
    );
  }
  return children;
}

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

  const visibleMenus = getVisibleMenus(role);
  const selectedKey = (visibleMenus.find((m) => location.pathname.startsWith(m.key))?.key || visibleMenus[0]?.key || "/jobs") as MenuKey;

  return (
    <Layout style={{ minHeight: "100vh" }}>
      <Sider collapsible>
        <div style={{ height: 48, color: "#fff", textAlign: "center", lineHeight: "48px", fontWeight: 600 }}>
          招聘 AI 助手
        </div>
        <Menu
          theme="dark"
          selectedKeys={[selectedKey]}
          items={visibleMenus}
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
            <Route path="/" element={<Navigate to={visibleMenus[0]?.key ?? "/jobs"} replace />} />
            <Route path="/jobs"       element={<RequirePermission role={role} path="/jobs"><JobPage /></RequirePermission>} />
            <Route path="/resumes"    element={<RequirePermission role={role} path="/resumes"><ResumePage /></RequirePermission>} />
            <Route path="/interviews" element={<RequirePermission role={role} path="/interviews"><InterviewPage /></RequirePermission>} />
            <Route path="/analytics"  element={<RequirePermission role={role} path="/analytics"><AnalyticsPage /></RequirePermission>} />
            <Route path="*" element={<Navigate to={visibleMenus[0]?.key ?? "/jobs"} replace />} />
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
