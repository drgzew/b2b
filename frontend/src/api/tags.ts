import { apiClient } from "./client";
import type {
    Tag
} from "./types";


export async function getAll()
:Promise<Tag[]> {

    const response =
        await apiClient.get(
            "/tags"
        );

    return response.data;

}