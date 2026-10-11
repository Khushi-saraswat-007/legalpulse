import axios from "axios";

// Base URL comes from frontend/.env (VITE_API_URL)
const client = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000",
});

// Attach the login token (when auth is ready) to every request
client.interceptors.request.use((config) => {
  const token = localStorage.getItem("lp_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export default client;
