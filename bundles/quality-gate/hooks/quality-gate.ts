const CODE_EXTENSIONS = new Set([
  ".ts",
  ".tsx",
  ".js",
  ".jsx",
  ".py",
  ".go",
  ".rs",
  ".java",
  ".rb",
  ".c",
  ".cpp",
  ".h",
  ".hpp",
  ".cs",
  ".swift",
  ".kt",
  ".scala",
  ".sh",
  ".bash",
]);

interface FileChange {
  path: string;
  hunks?: string;
}

interface ReviewIssue {
  file: string;
  line?: number;
  severity: "critical" | "high" | "medium" | "low";
  message: string;
}

interface HookContext {
  sessionId: string;
  modifiedFiles: FileChange[];
  delegateToAgent: (agentName: string, prompt: string) => Promise<string>;
  continueWithMessage: (message: string) => void;
}

const EXCLUDED_PATHS = [
  ".opencode/",
  ".cursor/",
  ".claude/",
  ".windsurf/",
  ".clinerules/",
  ".roo/",
  "node_modules/",
  ".git/",
  "bundles/quality-gate/",
];

function isExcluded(filePath: string): boolean {
  return EXCLUDED_PATHS.some((p) => filePath.startsWith(p));
}

function hasCodeChanges(files: FileChange[]): boolean {
  return files.some((f) => {
    if (isExcluded(f.path)) return false;
    const ext = f.path.slice(f.path.lastIndexOf("."));
    return CODE_EXTENSIONS.has(ext);
  });
}

function getCodeFiles(files: FileChange[]): FileChange[] {
  return files.filter((f) => {
    if (isExcluded(f.path)) return false;
    const ext = f.path.slice(f.path.lastIndexOf("."));
    return CODE_EXTENSIONS.has(ext);
  });
}

function parseReviewOutput(output: string): ReviewIssue[] {
  const issues: ReviewIssue[] = [];
  const lines = output.split("\n");

  for (const line of lines) {
    const match = line.match(
      /^(?:\[?(critical|high|medium|low)\]?)\s*[:\-–]\s*(?:(.+?):(\d+)\s*[:\-–]\s*)?(.+)/i,
    );
    if (match) {
      issues.push({
        severity: match[1].toLowerCase() as ReviewIssue["severity"],
        file: match[2] ?? "unknown",
        line: match[3] ? Number.parseInt(match[3], 10) : undefined,
        message: match[4].trim(),
      });
    }
  }

  return issues;
}

function formatIssuesForAgent(issues: ReviewIssue[]): string {
  const blocking = issues.filter(
    (i) => i.severity === "critical" || i.severity === "high",
  );
  const nonBlocking = issues.filter(
    (i) => i.severity === "medium" || i.severity === "low",
  );

  const lines: string[] = [];

  if (blocking.length > 0) {
    lines.push(
      `## ${blocking.length} blocking issue(s) — must fix before stopping\n`,
    );
    for (const issue of blocking) {
      const location = issue.line ? `${issue.file}:${issue.line}` : issue.file;
      lines.push(
        `- **[${issue.severity.toUpperCase()}]** ${location} — ${issue.message}`,
      );
    }
  }

  if (nonBlocking.length > 0) {
    lines.push(
      `\n## ${nonBlocking.length} non-blocking issue(s) — reported for awareness\n`,
    );
    for (const issue of nonBlocking) {
      const location = issue.line ? `${issue.file}:${issue.line}` : issue.file;
      lines.push(`- [${issue.severity}] ${location} — ${issue.message}`);
    }
  }

  return lines.join("\n");
}

function buildReviewPrompt(codeFiles: FileChange[]): string {
  const fileList = codeFiles.map((f) => `- ${f.path}`).join("\n");

  return [
    "Review the following modified code files. Focus ONLY on the changes, not the entire file.",
    "",
    "Modified files:",
    fileList,
    "",
    "For each issue found, output exactly one line in this format:",
    "[SEVERITY] - file:line - description",
    "",
    "Where SEVERITY is one of: critical, high, medium, low",
    "",
    "Severity guide:",
    "- critical: security vulnerabilities, data loss, crashes, broken auth",
    "- high: logic errors, missing error handling, race conditions, type safety violations",
    "- medium: code duplication, poor naming, missing edge cases",
    "- low: style preferences, minor readability improvements",
    "",
    "Do NOT flag formatting or style issues — linters handle those.",
    "If no issues found, output: NO_ISSUES_FOUND",
  ].join("\n");
}

export async function qualityGate(ctx: HookContext): Promise<void> {
  if (!hasCodeChanges(ctx.modifiedFiles)) {
    return;
  }

  const codeFiles = getCodeFiles(ctx.modifiedFiles);
  const prompt = buildReviewPrompt(codeFiles);
  const reviewOutput = await ctx.delegateToAgent("code-reviewer", prompt);

  if (reviewOutput.includes("NO_ISSUES_FOUND")) {
    return;
  }

  const issues = parseReviewOutput(reviewOutput);
  if (issues.length === 0) {
    return;
  }

  const hasBlocking = issues.some(
    (i) => i.severity === "critical" || i.severity === "high",
  );

  if (hasBlocking) {
    ctx.continueWithMessage(
      [
        "## Quality Gate — BLOCKED\n",
        "Code review found issues that must be fixed before completion.\n",
        formatIssuesForAgent(issues),
        "\nFix the critical and high issues above, then the quality gate will re-run automatically.",
      ].join("\n"),
    );
    return;
  }

  ctx.continueWithMessage(
    [
      "## Quality Gate — PASSED\n",
      "No blocking issues. The following were noted for awareness:\n",
      formatIssuesForAgent(issues),
    ].join("\n"),
  );
}

const _runCount = new Map<string, number>();

export default async function handler(
  event: { type: string; properties?: Record<string, unknown> },
  ctx: {
    client: { session: { prompt: (opts: unknown) => Promise<unknown> } };
    $: (
      strings: TemplateStringsArray,
      ...args: unknown[]
    ) => { text: () => Promise<string> };
  },
): Promise<void> {
  const rawSessionId = event.properties?.sessionID;
  const sessionId = typeof rawSessionId === "string" ? rawSessionId : "";
  if (!sessionId) return;

  let changedFiles: FileChange[] = [];
  try {
    const unstaged = await ctx.$`git diff --name-only HEAD 2>/dev/null`.text();
    const staged =
      await ctx.$`git diff --cached --name-only 2>/dev/null`.text();
    const untracked =
      await ctx.$`git ls-files --others --exclude-standard 2>/dev/null`.text();
    const all = `${unstaged}\n${staged}\n${untracked}`
      .split("\n")
      .filter(Boolean);
    changedFiles = [...new Set(all)].map((p) => ({ path: p }));
  } catch {
    return;
  }

  if (!hasCodeChanges(changedFiles)) return;

  const run = (_runCount.get(sessionId) ?? 0) + 1;
  _runCount.set(sessionId, run);

  const codeFiles = getCodeFiles(changedFiles);
  const fileList = codeFiles.map((f) => `- ${f.path}`).join("\n");

  let prompt: string;

  if (run === 1) {
    let diffContent = "";
    try {
      diffContent = (await ctx.$`git diff HEAD 2>/dev/null`.text()).trim();
    } catch {}

    prompt = [
      "## Quality Gate — Code Review\n",
      "Review these modified files for bugs, security issues, and correctness:",
      fileList,
      "",
      diffContent
        ? `\`\`\`diff\n${diffContent}\n\`\`\``
        : "Run `git diff HEAD` to see changes.",
      "\nRules:",
      "- If you find critical or high severity issues: fix them immediately. Do NOT finish until they are all resolved.",
      "- If only medium/low issues: note them and finish.",
      "- If no issues: say NO_ISSUES_FOUND and finish.",
    ].join("\n");
  } else {
    prompt = `Quality gate re-check #${run}. Are the critical/high issues from the previous review fixed? Check ${fileList}. If all fixed, finish. If not, fix them now.`;
  }

  try {
    await ctx.client.session.prompt({
      path: { id: sessionId },
      body: { parts: [{ type: "text", text: prompt }] },
    });
  } catch {}
}

export {
  hasCodeChanges,
  getCodeFiles,
  parseReviewOutput,
  formatIssuesForAgent,
  buildReviewPrompt,
};
export type { FileChange, ReviewIssue, HookContext };
