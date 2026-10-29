import client from "./client";

// POST /auth/forgot-password  (always answers the same, whether or not the email exists)
export const forgotPassword = (email) =>
  client.post("/auth/forgot-password", { email }).then((r) => r.data);

// POST /auth/reset-password  (token comes from the emailed link)
export const resetPassword = (token, password) =>
  client.post("/auth/reset-password", { token, password }).then((r) => r.data);