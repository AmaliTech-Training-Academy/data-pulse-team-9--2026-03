import { fetchApi } from "./api";

export interface User {
    id: number;
    email: string;
    full_name: string;
    role: string;
    created_at: string;
}

export async function getUsers(): Promise<User[]> {
    const response = await fetchApi("/auth/users");
    if (Array.isArray(response)) {
        return response;
    }
    return [];
}
