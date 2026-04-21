import axios from "axios";

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "https://aurelius-production-44e1.up.railway.app/api",
});
