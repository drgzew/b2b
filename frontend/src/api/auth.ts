import {apiClient} from "./client";

export interface LoginResponse {
    access_token:string;
    role:string;
}

export async function login(
    email:string,
    password:string
){
    const response =
        await apiClient.post<LoginResponse>(
            "/auth/login",
            {
                email,
                password
            }
        );

    return response.data;
}