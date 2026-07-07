import type {ArtifactRequest} from "../api/types";

export const requests:ArtifactRequest[] = [

    {
        id:1,
        artifactId:1,
        artifactTitle:
            "Моделирование фильтрации нефти",
        requester:
            "Иванов Иван",
        requesterRole:
            "Студент",
        status:
            "pending",
        createdAt:
            "2026-01-10"
    },


    {
        id:2,
        artifactId:3,
        artifactTitle:
            "Оптимизация системы поддержания пластового давления",
        requester:
            "ООО Нефтегаз",
        requesterRole:
            "Партнёр",
        status:
            "approved",
        createdAt:
            "2026-01-12"
    }

];