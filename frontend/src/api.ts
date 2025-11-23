// src/api.ts
import axios from "axios";
import { AuthResponse, UserInfo } from "./types";

export async function sendAuthMessage(
  message: string,
  user_info: UserInfo,
  system_last_message: string
): Promise<AuthResponse> {
  const res = await axios.post<AuthResponse>("http://localhost:8000/auth", {
    message,
    user_info,
    system_last_message,
  });

  return res.data; 
}

// RAG ROUTE
export async function sendRagMessage(
  user_message: string,
  user_info: UserInfo
) {
  const res = await axios.post("http://localhost:8000/rag", {
    user_message,
    user_info,
  });

  return res.data; 
}
