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
};

export type Case = {
  case_id: string;
  organization_id: string;
  status: string;
  priority?: string;
};