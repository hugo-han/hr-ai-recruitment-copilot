import { describe, it, expect } from "vitest";
import { getVisibleMenus } from "../App";

// 直接测 getVisibleMenus 纯函数（不依赖 React 渲染）
// 对应 Issue #4 验收标准

describe("getVisibleMenus — 角色菜单过滤", () => {
  it("HR 只能看 job/resume/interview，无 analytics", () => {
    const menus = getVisibleMenus("HR");
    const keys = menus.map((m) => m.key);
    expect(keys).toContain("/jobs");
    expect(keys).toContain("/resumes");
    expect(keys).toContain("/interviews");
    expect(keys).not.toContain("/analytics");
  });

  it("HR_LEAD 可以看全部 4 个菜单", () => {
    const menus = getVisibleMenus("HR_LEAD");
    const keys = menus.map((m) => m.key);
    expect(keys).toContain("/analytics");
    expect(keys).toHaveLength(4);
  });

  it("INTERVIEWER 只能看 interview", () => {
    const menus = getVisibleMenus("INTERVIEWER");
    const keys = menus.map((m) => m.key);
    expect(keys).toEqual(["/interviews"]);
  });

  it("ADMIN 可以看全部 4 个菜单", () => {
    const menus = getVisibleMenus("ADMIN");
    expect(menus).toHaveLength(4);
  });

  it("未知角色回退到 HR 三项", () => {
    const menus = getVisibleMenus("UNKNOWN_ROLE");
    const keys = menus.map((m) => m.key);
    expect(keys).not.toContain("/analytics");
    expect(keys).toContain("/jobs");
  });
});
