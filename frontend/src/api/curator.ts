import { apiClient } from "./client";
import type {
    Artifact,
    ArtifactRequest
} from "./types";

export async function getCuratorArtifacts(
    status?: string
): Promise<Artifact[]> {

    const response =
        await apiClient.get(
            "/curator/artifacts",
            {
                params:{
                    status
                }
            }
        );

    return response.data;
}


export async function getArtifact(
    id:number
): Promise<Artifact> {

    const response =
        await apiClient.get(
            `/artifacts/${id}`
        );

    return response.data;
}


export async function updateArtifactTags(
    id:number,
    tagIds:number[]
): Promise<Artifact> {

    const response =
        await apiClient.put(
            `/curator/artifacts/${id}/tags`,
            {
                tag_ids:tagIds
            }
        );

    return response.data;
}


export async function approveArtifact(
    id:number
): Promise<Artifact> {

    const response =
        await apiClient.post(
            `/curator/artifacts/${id}/approve`
        );

    return response.data;
}


export async function rejectArtifact(
    id:number
): Promise<Artifact> {

    const response =
        await apiClient.post(
            `/curator/artifacts/${id}/reject`
        );

    return response.data;
}


export async function getRequests()
:Promise<ArtifactRequest[]> {

    const response =
        await apiClient.get(
            "/curator/requests"
        );

    return response.data;
}


export async function updateRequestStatus(
    id:number,
    status:string
):Promise<ArtifactRequest> {

    const response =
        await apiClient.patch(
            `/curator/requests/${id}`,
            {
                status
            }
        );

    return response.data;
}