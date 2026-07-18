import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { BrowserRouter } from "react-router-dom";
import InterviewPage from "../pages/InterviewPage";

vi.mock("../api/interview", () => ({
  createInterview: vi.fn().mockResolvedValue({ interview_id: 1, status: "recorded" }),
  evaluateInterview: vi.fn().mockResolvedValue({
    interview_id: 1,
    summary: "候选人表现优秀",
    capability_eval: { "专业技能": "符合", "沟通表达": "良好", "解决问题": "优秀", "团队协作": "良好", "学习能力": "符合" },
    recommendation: "推荐",
    rationale: { "专业技能": "经验丰富" },
  }),
}));

function renderWithRouter(ui: React.ReactElement) {
  return render(<BrowserRouter>{ui}</BrowserRouter>);
}

describe("InterviewPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders interview form with two-step buttons", () => {
    renderWithRouter(<InterviewPage />);
    expect(screen.getByText("AI 面试助手")).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/输入面试/)).toBeInTheDocument();
    // Fix #12: 拆分为「保存记录」+ 「生成评价」两个按钮
    const saveButtons = screen.getAllByText("保存记录");
    expect(saveButtons.length).toBeGreaterThan(0);
  });

  it("requires record text before submit", async () => {
    const user = userEvent.setup();
    renderWithRouter(<InterviewPage />);
    const saveBtn = screen.getAllByText("保存记录")[0];
    await user.click(saveBtn);
    await waitFor(() => {
      expect(screen.getByText(/请输入面试记录/)).toBeInTheDocument();
    });
  });

  it("saves record and calls createInterview", async () => {
    const user = userEvent.setup();
    const { createInterview } = await import("../api/interview");

    renderWithRouter(<InterviewPage />);
    await user.type(screen.getByPlaceholderText(/输入面试/), "面试记录内容...");
    const saveBtn = screen.getAllByText("保存记录")[0];
    await user.click(saveBtn);

    await waitFor(() => {
      expect(createInterview).toHaveBeenCalledWith(
        expect.objectContaining({ record_text: "面试记录内容..." })
      );
    });
    // evaluateInterview 此时不应自动触发（Fix #12 核心验证）
    const { evaluateInterview } = await import("../api/interview");
    expect(evaluateInterview).not.toHaveBeenCalled();
  });
});
