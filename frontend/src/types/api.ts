export type ApiEnvelope<T> = {
  data: T;
};

export type HealthResponse = ApiEnvelope<{
  status: string;
  service: string;
  api_version?: string;
}>;

export type User = {
  user_id: string;
  organization_id: string;
  email: string;
  role: string;
};

export type Review = {
  review_id: string;
  organization_id: string;
  rating: number;
  text: string;
  source: string;
  review_url?: string | null;
  published_at?: string | null;
  author_display_name?: string | null;
  location_id?: string;
  language?: string | null;
  updated_at?: string | null;
};

export type Case = {
  case_id: string;
  organization_id: string;
  status: string;
  priority?: string;
  created_at?: string | null;
  review_id?: string;
};
export type ReviewQueueItem = {
  case_id: string;
  priority?: string;
  priority_score?: number;
  status: string;
  assigned_to?: string | null;
  sla?: { status?: string; due_at?: string | null };
};

export type NotificationItem = {
  notification_id: string;
  status: string;
  created_at?: string | null;
  subject?: string;
  body?: string;
};

export type AdminMember = {
  user_id: string;
  email: string;
  role: string;
};

export type InvitationResponse = {
  invitation_id?: string;
  organization_id?: string;
  email?: string;
  role?: string;
  expires_at?: string;
  invited_by?: string;
  invitation_token?: string;
};
