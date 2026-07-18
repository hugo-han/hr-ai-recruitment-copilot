import { Layout, Menu, theme } from "antd";
import { Routes, Route, Navigate } from "react-router-dom";
import DashboardPage from "./pages/DashboardPage";

const { Header, Content, Sider } = Layout;

const menuItems = [
  { key: "jobs", label: "AI 职位助手" },
  { key: "resumes", label: "AI 简历分析" },
  { key: "interviews", label: "AI 面试助手" },
  { key: "analytics", label: "数据分析" },
];

export default function App() {
  const {
    token: { colorBgContainer },
  } = theme.useToken();

  return (
    <Layout style={{ minHeight: "100vh" }}>
      <Sider collapsible>
        <div style={{ height: 48, color: "#fff", textAlign: "center", lineHeight: "48px" }}>
          招聘 AI 助手
        </div>
        <Menu theme="dark" defaultSelectedKeys={["jobs"]} items={menuItems} />
      </Sider>
      <Layout>
        <Header style={{ background: colorBgContainer, padding: "0 24px" }}>HR 招聘 AI 助手</Header>
        <Content style={{ margin: "24px 16px", padding: 24, background: colorBgContainer }}>
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="*" element={<DashboardPage />} />
          </Routes>
        </Content>
      </Layout>
    </Layout>
  );
}
