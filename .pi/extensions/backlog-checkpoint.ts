import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { execFileSync } from "node:child_process";
import { existsSync, readdirSync, statSync } from "node:fs";
import { join, relative } from "node:path";

/**
 * Backlog checkpoint guardrail.
 *
 * On /new, refresh the generated backlog/context files and block the switch
 * if source files changed since the last session checkpoint (commit-independent,
 * so it works even without committing).
 */

const CHECKPOINT = "product/context/SESSION_CHECKPOINT.json";

const EXCLUDE_DIRS = new Set([
  ".git",
  ".pi",
  "node_modules",
  ".venv",
  "venv",
  "__pycache__",
  "static",
  "media",
]);

const EXCLUDE_FILES = new Set([
  "db.sqlite3",
  "test_db.sqlite3",
  ".env",
  "product/backlog.md",
  "product/context/CURRENT_STATE.md",
  CHECKPOINT,
]);

function runPython(script: string, cwd: string): void {
  for (const py of ["python", "python3", "py"]) {
    try {
      execFileSync(py, [script], { cwd, stdio: "ignore", timeout: 60000 });
      return;
    } catch {
      // try the next interpreter
    }
  }
}

function latestMtime(root: string): number {
  let latest = 0;
  const walk = (dir: string): void => {
    let entries;
    try {
      entries = readdirSync(dir, { withFileTypes: true });
    } catch {
      return;
    }
    for (const entry of entries) {
      const full = join(dir, entry.name);
      if (entry.isDirectory()) {
        if (EXCLUDE_DIRS.has(entry.name)) continue;
        walk(full);
      } else if (entry.isFile()) {
        const rel = relative(root, full).replace(/\\/g, "/");
        if (EXCLUDE_FILES.has(rel) || rel.endsWith(".pyc")) continue;
        try {
          const m = statSync(full).mtimeMs;
          if (m > latest) latest = m;
        } catch {
          // ignore unreadable files
        }
      }
    }
  };
  walk(root);
  return latest;
}

function checkStale(cwd: string): boolean {
  const checkpoint = join(cwd, CHECKPOINT);
  if (!existsSync(checkpoint)) return true; // no checkpoint yet
  const checkpointMtime = statSync(checkpoint).mtimeMs;
  return latestMtime(cwd) > checkpointMtime;
}

export default function (pi: ExtensionAPI) {
  pi.on("session_before_switch", async (event, ctx) => {
    if (event.reason !== "new") return;

    const cwd = ctx.cwd;
    // Scope guard: only act in repos with the River backlog markers.
    if (!existsSync(join(cwd, "product", "backlog.py"))) return;

    // Always refresh the mechanical outputs (best-effort).
    runPython("product/backlog.py", cwd);
    runPython("summarise.py", cwd);

    // If nothing changed since the last checkpoint, allow /new.
    if (!checkStale(cwd)) return;

    // Default = cancel (auto-cancels on timeout).
    const proceed = await ctx.ui.confirm(
      "Backlog checkpoint stale",
      "Files changed since the last session checkpoint. Close the loop first " +
        '(tell me: "close the loop" or "update the backlog") before starting fresh.\n\n' +
        "Proceed with /new anyway?",
      { timeout: 15000 },
    );

    if (!proceed) {
      return { cancel: true };
    }
  });
}
