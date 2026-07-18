import axios from "axios";

// 统一请求实例：附加 Authorization、解包统一响应结构
export const api = axios.create({ baseURL: "/api", timeout: 30000 });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (resp) => {
    const body = resp.data;
    if (body && typeof body === "object" && "code" in body) {
      if (body.code !== 0) {
        return Promise.reject(new Error(body.message || "请求失败"));
      }
      return { ...resp, data: body.data };
    }
    return resp;
  },
  (error) => Promise.reject(error)
);

export interface ApiResult<T> {
  data: T;
}
