export type ArtifactStatus =
    | "draft"
    | "approved"
    | "rejected";

export type ArtifactType =
    | "vkr"
    | "article"
    | "talk"
    | "event";

export type RequestStatus =
    | "sent"
    | "in_progress"
    | "done";

export interface Tag {
    id:number;
    name:string;
}

export interface Artifact {
    id:number;
    title:string;
    type:ArtifactType;
    annotation:string;
    file_path?:string;
    curator_status:ArtifactStatus;
    access_level:string;
    author_name?:string;
    created_at:string;
    tags:Tag[];
}

export interface ArtifactRequest {
    id:number;
    artifact_id:number;
    partner_id:number;
    type:string;
    status:RequestStatus;
    created_at:string;
}

export interface ArtifactRequest {
    id:number;
    artifact:{
        id:number;
        title:string;
    };
    partner:{
        id:number;
        name:string;
    };
    type:string;
    status: RequestStatus;
    created_at:string;
}


export interface Subscription {
  id: number;
  name: string;
  tags: string[];
  description?: string;
}

export interface DigestItem {
  artifact: Artifact;
  relevance: number;
}

export interface RequestPayload {
  artifact_id: number;
  type: 'full_text' | 'internship' | 'rnd';
}