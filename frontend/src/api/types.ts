export type ArtifactStatus =
    | "moderation"
    | "published"
    | "rejected";

export type ArtifactType =
    | "vkr"
    | "article"
    | "talk"
    | "event";

export type RequestStatus =
    | "pending"
    | "approved"
    | "rejected";

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

export interface ArtifactRequest {
    id:number;
    artifactId:number;
    artifactTitle:string;
    requester:string;
    requesterRole:string;
    status:RequestStatus;
    createdAt:string;
}