import { fetchApi } from "./api";

export const AuthService = {
  login: async (email: string, password: string) => {
    return fetchApi("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
  },

  register: async (full_name: string, email: string, password: string) => {
    return fetchApi("/auth/register", {
      method: "POST",
      body: JSON.stringify({ full_name, email, password }),
    });
  },

  getMe: async (token: string) => {
    return fetchApi("/auth/me", {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
  },
};
