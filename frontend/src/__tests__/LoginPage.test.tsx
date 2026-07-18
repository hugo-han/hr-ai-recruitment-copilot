import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { BrowserRouter } from "react-router-dom";
import LoginPage from "../pages/LoginPage";

// Mock the auth API
vi.mock("../api/auth", () => ({
  login: vi.fn().mockResolvedValue({
    access_token: "fake-token",
    refresh_token: "fake-refresh",
    token_type: "bearer",
    role: "HR",
    name: "测试HR",
  }),
  getMe: vi.fn().mockResolvedValue({
    id: 1,
    username: "hr",
    name: "测试HR",
    role: "HR",
  }),
}));

// Mock zustand store
const mockSetAuth = vi.fn();
vi.mock("../store/auth", () => ({
  useAuthStore: vi.fn().mockImplementation((selector) => {
    const state = {
      token: null,
      role: "",
      name: "",
      setAuth: mockSetAuth,
      logout: vi.fn(),
      isLoggedIn: () => false,
    };
    return selector ? selector(state) : state;
  }),
}));

function renderWithRouter(ui: React.ReactElement) {
  return render(<BrowserRouter>{ui}</BrowserRouter>);
}

describe("LoginPage", () => {
  it("renders login form", () => {
    renderWithRouter(<LoginPage />);
    expect(screen.getByPlaceholderText("用户名")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("密码")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /登录/ })).toBeInTheDocument();
  });

  it("shows validation error when submitting empty form", async () => {
    renderWithRouter(<LoginPage />);
    const btn = screen.getByRole("button", { name: /登录/ });
    fireEvent.click(btn);
    await waitFor(() => {
      expect(screen.getByText(/请输入用户名/)).toBeInTheDocument();
      expect(screen.getByText(/请输入密码/)).toBeInTheDocument();
    });
  });

  it("calls login API on valid submit", async () => {
    const user = userEvent.setup();
    const { login } = await import("../api/auth");

    renderWithRouter(<LoginPage />);
    await user.type(screen.getByPlaceholderText("用户名"), "hr");
    await user.type(screen.getByPlaceholderText("密码"), "hr123");
    await user.click(screen.getByRole("button", { name: /登录/ }));

    await waitFor(() => {
      expect(login).toHaveBeenCalledWith("hr", "hr123");
    });
  });
});
