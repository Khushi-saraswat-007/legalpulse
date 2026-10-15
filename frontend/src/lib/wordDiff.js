// Tiny word-level diff (longest common subsequence) so the Changes page needs no extra library.
// Returns the two texts as token lists: [{ t: "word", changed: true|false }, ...] for the old and the new text.
export function wordDiff(oldText = "", newText = "") {
  const a = oldText.split(/(\s+)/).filter((t) => t !== "");
  const b = newText.split(/(\s+)/).filter((t) => t !== "");
  const plain = (tokens) => tokens.map((t) => ({ t, changed: false }));
  if (a.length * b.length > 4_000_000) return { left: plain(a), right: plain(b) }; // very long clause: skip highlighting

  const n = a.length, m = b.length;
  const dp = Array.from({ length: n + 1 }, () => new Uint16Array(m + 1));
  for (let i = n - 1; i >= 0; i--) {
    for (let j = m - 1; j >= 0; j--) {
      dp[i][j] = a[i] === b[j] ? dp[i + 1][j + 1] + 1 : Math.max(dp[i + 1][j], dp[i][j + 1]);
    }
  }

  const left = [], right = [];
  let i = 0, j = 0;
  while (i < n && j < m) {
    if (a[i] === b[j]) { left.push({ t: a[i], changed: false }); right.push({ t: b[j], changed: false }); i++; j++; }
    else if (dp[i + 1][j] >= dp[i][j + 1]) { left.push({ t: a[i], changed: !/^\s+$/.test(a[i]) }); i++; }
    else { right.push({ t: b[j], changed: !/^\s+$/.test(b[j]) }); j++; }
  }
  for (; i < n; i++) left.push({ t: a[i], changed: !/^\s+$/.test(a[i]) });
  for (; j < m; j++) right.push({ t: b[j], changed: !/^\s+$/.test(b[j]) });
  return { left, right };
}
