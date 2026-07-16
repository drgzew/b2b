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
    | "accepted"
    | "in_progress"
    | "rejected"
    | "completed";
export type RequestType =
    | "full_text"
    | "internship"
    | "rnd";

export interface Tag {
  id: number;
  name: string;
}

export interface Artifact {
  id: number;
  title: string;
  type: 'vkr' | 'article' | 'talk' | 'event';
  annotation: string;
  file_path?: string | null;
  curator_status: 'draft' | 'approved' | 'rejected';
  read_policy: 'open' | 'requires_approval';
  created_at: string;
  tags: Tag[];
  author_id?: number | null;
  author_name?: string | null;
  supervisor_id?: number | null;
  supervisor_name?: string | null;
}

export interface Author {
  id: number;
  email?: string | null;
  full_name: string;
  photo_url?: string | null;
  birth_date?: string | null;
  program?: string | null;
  job_status: 'searching' | 'not_searching' | 'employed';
}

export interface Teacher {
  id: number;
  full_name: string;
  email: string;
  department: string;
  position: string;
}

export interface Subscription {
  id: number;
  name: string;
  tags: string[];
  description?: string;
}

export interface DigestEntry {
  artifact: Artifact;
  relevance: number;
  can_read: boolean;
}

export interface Favorite {
  id: number;
  artifact_id: number;
  partner_id: number;
  added_at: string;
  artifact: Artifact;
}

export interface Internship {
  id: number;
  artifact_id: number;
  partner_id: number;
  partner_name?: string;
  status: 'sent' | 'accepted' | 'in_progress' | 'rejected' | 'completed' | 'cancelled';
  student_name: string;
  created_at: string;
  response_date?: string | null;
  artifact_title?: string;
  artifact?: Artifact;
}

export interface Request {
  id: number;
  artifact_id: number;
  partner_id: number;
  type: 'full_text' | 'internship' | 'rnd';
  status: 'sent' | 'in_progress' | 'done' | 'rejected' | 'approved';
  created_at: string;
}

export interface AuthorRequest {
  id: number;
  artifact_id: number;
  artifact_title: string;
  partner_id: number;
  partner_name: string;
  type: string;
  status: string;
  created_at: string;
}

export interface ReadAccessResponse {
  mode: 'redirect' | 'pdf';
  url?: string | null;
}

export interface LoginResponse {
  access_token: string;
  role: string;
}

export interface PartnerRead {
  id: number;
  name: string;
  contact_email: string;
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
    type: RequestType;
    status: RequestStatus;
    created_at:string;
}

export interface PartnerRequest {
    id:number;
    artifact:{
        author_name: string;
        id:number;
        title:string;
        type:ArtifactType;
    };
    partner:{
        id:number;
        name:string;
    };
    author:{
        id:number;
        name:string;
    };
    type:RequestType;
    status:RequestStatus;
    curator_comment?:string;
    created_at:string;
    updated_at?:string;
}