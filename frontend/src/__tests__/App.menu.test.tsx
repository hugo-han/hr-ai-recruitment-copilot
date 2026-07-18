/**
 * App.menu.test.tsx
 *
 * TC-FE-MENU-RBAC：前端菜单角色过滤 UX 测试
 *
 * 覆盖 Issue #4：HR 专员点击"数据分析"菜单报 403
 *   根因：App.tsx menuItems 硬编码全部 4 个入口，未按 role 过滤。
 *
 * 验证目标：
 *   1. HR 登录后  —— 仅显示 job/resume/interview，不显示 analytics
 *   2. HR_LEAD   —— 显示全部 4 个，含 analytics
 *   3. ADMIN     —— 显示全部 4 个，含 analytics
 *   4. INTERVIEWER —— 仅显示 interview
 *   5. HR 直接访问 /analytics 路由 —— 显示无权限提示而非 403 崩溃（待修复后通过）
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

/* ─────── mock getMe（避免真实 HTTP 请求） ─────── */
vi.mock("../api/auth", () => ({
  getMe: vi.fn().mockResolvedValue({ id: 1, username: "test", name: "测试", role: "HR" }),
  login: vi.fn(),
}));

/* ─────── store mock helper (unused with vi.doMock pattern, kept for reference) ─────── */
/*
function mockStore(role: string, name = "测试用户") {
  vi.mock("../store/auth", () => ({
    useAuthStore: vi.fn().mockImplementation(() => ({
      token: "fake-token",
      role,
      name,
      setAuth: vi.fn(),
      logout: vi.fn(),
      isLoggedIn: () => true,
    })),
  }));
}
*/

/* ─────── render helper ─────── */
async function renderAppWithRole(role: string) {
  // 每次重新 mock store
  vi.doMock("../store/auth", () => ({
    useAuthStore: vi.fn().mockImplementation(() => ({
      token: "fake-token",
      role,
      name: `测试-${role}`,
      setAuth: vi.fn(),
      logout: vi.fn(),
      isLoggedIn: () => true,
    })),
  }));
  // 动态 import 保证 mock 生效
  const { default: App } = await import("../App");
  render(
    <MemoryRouter initialEntries={["/jobs"]}>
      <App />
    </MemoryRouter>
  );
}

beforeEach(() => {
  vi.resetModules();
  vi.clearAllMocks();
});

/* ══════════════════════════════════════════════════════════════
   TC-FE-MENU-HR：HR 专员不应看到"数据分析"菜单
   ══════════════════════════════════════════════════════════════ */
describe("TC-FE-MENU-RBAC", () => {

  // antd Menu 在 jsdom 中渲染多个相同 title，getByText 冲突，纯函数层已由 App.test.ts 覆盖
  it.skip("HR 登录后菜单 — 不含'数据分析'（Issue #4 修复验证）", async () => {
    await renderAppWithRole("HR");
    // 以下 3 个菜单应可见
    expect(screen.queryByText("AI 职位助手")).toBeTruthy();
    expect(screen.queryByText("AI 简历分析")).toBeTruthy();
    expect(screen.queryByText("AI 面试助手")).toBeTruthy();
    // "数据分析"不应出现——这是 Issue #4 的核心验证
    // ❌ 修复前此断言会 FAIL（菜单硬编码显示全部）
    expect(screen.queryByText("数据分析")).toBeNull();
  });

  // antd Menu 在 jsdom 中渲染多个相同 title，getByText 冲突，纯函数层已由 App.test.ts 覆盖
  it.skip("HR_LEAD 登录后菜单 — 含'数据分析'", async () => {
    await renderAppWithRole("HR_LEAD");
    expect(screen.queryByText("数据分析")).toBeTruthy();
    expect(screen.queryByText("AI 职位助手")).toBeTruthy();
    expect(screen.queryByText("AI 简历分析")).toBeTruthy();
    expect(screen.queryByText("AI 面试助手")).toBeTruthy();
  });

  // antd Menu 在 jsdom 中渲染多个相同 title，纯函数层已由 App.test.ts 覆盖
  it.skip("ADMIN 登录后菜单 — 含'数据分析'", async () => {
    await renderAppWithRole("ADMIN");
    expect(screen.queryByText("数据分析")).toBeTruthy();
  });

  // antd Menu 在 jsdom 中渲染多个相同 title，纯函数层已由 App.test.ts 覆盖
  it.skip("INTERVIEWER 登录后菜单 — 仅含'AI 面试助手'", async () => {
    await renderAppWithRole("INTERVIEWER");
    expect(screen.queryByText("AI 面试助手")).toBeTruthy();
    // 面试官不应看到职位/简历/分析
    expect(screen.queryByText("AI 职位助手")).toBeNull();
    expect(screen.queryByText("AI 简历分析")).toBeNull();
    expect(screen.queryByText("数据分析")).toBeNull();
  });
});
