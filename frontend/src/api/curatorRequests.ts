import { apiClient } from "./client";
import type {
    PartnerRequest,
    RequestStatus
} from "./types";


export async function getCuratorRequests(
    status?: RequestStatus
): Promise<PartnerRequest[]> {

    const response = await apiClient.get(
        "/curator/requests",
        {
            params:{
                status
            }
        }
    );

    return response.data;
}



export async function getRequest(
    id:number
):Promise<PartnerRequest>{

    const response =
        await apiClient.get(
            `/curator/requests/${id}`
        );

    return response.data;
}



export async function takeRequest(
    id:number
):Promise<PartnerRequest>{

    const response =
        await apiClient.patch(
            `/curator/requests/${id}`,
            {
                status:"in_progress"
            }
        );

    return response.data;
}



export async function updateRequestStatus(
    id:number,
    status:RequestStatus,
    comment?:string
):Promise<PartnerRequest>{

    const response =
        await apiClient.patch(
            `/curator/requests/${id}`,
            {
                status,
                comment
            }
        );


    return response.data;
}



export async function getRequestStats(){

    const response =
        await apiClient.get(
            "/curator/requests/stats"
        );

    return response.data;
}