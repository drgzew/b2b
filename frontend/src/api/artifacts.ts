import { apiClient } from "./client";
import type {
    Artifact
} from "./types";


export async function getArtifacts()
:Promise<Artifact[]> {

    const response =
        await apiClient.get(
            "/artifacts"
        );

    return response.data;

}


export async function getArtifact(
    id:number
)
:Promise<Artifact> {

    const response =
        await apiClient.get(
            `/artifacts/${id}`
        );

    return response.data;

}