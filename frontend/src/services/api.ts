import axios from "axios";

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "https://lightseagreen-bear-113896.hostingersite.com/api",
});
