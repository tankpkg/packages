import type { Plugin } from "@opencode-ai/plugin";

export const QualityGate: Plugin = async ({ client, $ }) => {
  const _reviewedFingerprints = new Set<string>();
  let _running = false;
  return {
    event: ({ event }) => {
      const e = event;
      if (e.type !== "session.idle") return;
      if (_running) return;
      const sid = e.properties?.sessionID ?? "";
      if (!sid) return;
      _running = true;
      $`git diff --stat HEAD 2>/dev/null`.text().then((stat) => {
        const fp = stat.trim();
        if (!fp || _reviewedFingerprints.has(fp)) {
          _running = false;
          return;
        }
        _reviewedFingerprints.add(fp);
        return import("./handlers/quality-gate.handler").then((handler) =>
          handler.default(e, { client, $ })
        );
      }).catch((err) => console.error("[quality-gate]", err)).finally(() => { _running = false; });
    },
  };
};
