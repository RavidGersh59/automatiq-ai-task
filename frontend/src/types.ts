export interface UserInfo {
  name: string | null;
  id: string | null;
  division: string | null;
}

export interface AuthResponse {
  user_info: UserInfo;
  system_last_message: string;
  authenticated: boolean;
}
