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

  it("renders interview form", () => {
    renderWithRouter(<InterviewPage />);
    expect(screen.getByText("AI 面试助手")).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/输入面试/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /提交/ })).toBeInTheDocument();
  });

  it("requires record text before submit", async () => {
    const user = userEvent.setup();
    renderWithRouter(<InterviewPage />);
    await user.click(screen.getByRole("button", { name: /提交/ }));
    await waitFor(() => {
      expect(screen.getByText(/请输入面试记录/)).toBeInTheDocument();
    });
  });

  it("submits and shows evaluation result", async () => {
    const user = userEvent.setup();
    const { createInterview, evaluateInterview } = await import("../api/interview");

    renderWithRouter(<InterviewPage />);
    await user.type(screen.getByPlaceholderText(/输入面试/), "面试记录内容...");
    await user.click(screen.getByRole("button", { name: /提交/ }));

    await waitFor(() => {
      expect(createInterview).toHaveBeenCalled();
      expect(evaluateInterview).toHaveBeenCalled();
    });

    await waitFor(() => {
      expect(screen.getByText("候选人表现优秀")).toBeInTheDocument();
      expect(screen.getByText("推荐")).toBeInTheDocument();
    });
  });
});
