import { apiClient } from "./client";
import type {
    PartnerRequest
} from "./types";


export async function getCuratorRequests(): Promise<PartnerRequest[]> {

    const response = await apiClient.get(
        "/curator/requests"
    );

    return response.data;
}


// Решение по запросу на полный текст: одобрить (выдаёт партнёру доступ
// к тексту через PartnerArtifactAccess) или отклонить.
// Бэкенд принимает решение только для type=full_text в статусе sent.
export async function decideRequest(
    id: number,
    approve: boolean
): Promise<PartnerRequest> {

    const response =
        await apiClient.post(
            `/curator/requests/${id}/decision`,
            {
                approve
            }
        );

    return response.data;
}


// Смена рабочего статуса запроса (для стажировок/НИОКР):
// бэкенд принимает только "in_progress" и "done".
export async function updateRequestStatus(
    id: number,
    status: "in_progress" | "done"
): Promise<PartnerRequest> {

    const response =
        await apiClient.patch(
            `/curator/requests/${id}/status`,
            {
                status
            }
        );

    return response.data;
}


export async function takeRequest(
    id: number
): Promise<PartnerRequest> {

    return updateRequestStatus(
        id,
        "in_progress"
    );
}
