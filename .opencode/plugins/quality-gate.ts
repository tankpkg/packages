import type { Plugin } from "@opencode-ai/plugin";

export const QualityGate: Plugin = async ({ client, $ }) => {
  let _lastFingerprint = "";
  let _running = false;
  return {
    event: ({ event }) => {
      const e = event;
      if (e.type !== "session.idle") return;
      if (_running) return;
      const sid = e.properties?.sessionID ?? "";
      if (!sid) return;
      _running = true;
      $`git status --porcelain 2>/dev/null`.text().then((stat) => {
        const fp = stat.trim();
        console.log("[quality-gate] fingerprint:", JSON.stringify(fp), "last:", JSON.stringify(_lastFingerprint));
        if (!fp || fp === _lastFingerprint) {
          _running = false;
          return;
        }
        _lastFingerprint = fp;
        console.log("[quality-gate] loading handler...");
        return import("./handlers/quality-gate.handler").then((handler) => {
          console.log("[quality-gate] handler loaded, calling default...");
          return handler.default(e, { client, $ });
        }).then(() => {
          console.log("[quality-gate] handler completed");
        });
      }).catch((err) => console.error("[quality-gate] ERROR:", err)).finally(() => { _running = false; });
    },
  };
};
