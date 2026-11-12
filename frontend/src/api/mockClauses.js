// TEMPORARY: clause text for the diff view.
// The risk report only has change summaries, not clause text, so this is
// placeholder data. Replace with real data once the backend exposes
// clause text (e.g. GET /contracts/{id}).
export const mockClauses = {
  c001_12: {
    heading: "Termination",
    text: "Either party may terminate with 30 days notice. Clause 9 penalties survive termination.",
  },
  c002_12: {
    heading: "Termination",
    text: "Either party may terminate with 90 days notice. Clause 9 penalties survive termination.",
  },
};
