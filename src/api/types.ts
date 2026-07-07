export type ArtifactStatus =
    | "moderation"
    | "published"
    | "rejected";


export type ArtifactType =
    | "vkr"
    | "article"
    | "Доклад"
    | "Мероприятие";

export interface Tag {
    id: number;
    name: string;
}

export interface Artifact {
    id: number;
    title: string;
    type: ArtifactType;
    annotation: string;
    file_path?: string;
    status: ArtifactStatus;
    access_level: string;
    author_name?: string;
    created_at: string;
    tags: Tag[];
}