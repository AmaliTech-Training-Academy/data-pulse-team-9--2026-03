import { fetchApi } from "./api";

export const AuthService = {
  login: async (email: string, password: string) => {
    return fetchApi("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
      skipAuth: true,
    });
  },

  register: async (full_name: string, email: string, password: string) => {
    return fetchApi("/api/auth/register", {
      method: "POST",
      body: JSON.stringify({ full_name, email, password }),
      skipAuth: true,
    });
  },

  getMe: async (token: string) => {
    return fetchApi("/api/auth/me", {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
  },
};
