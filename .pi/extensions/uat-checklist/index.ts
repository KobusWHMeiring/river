/**
 * UAT Checklist Extension
 *
 * Registers the `present_uat_tests` tool. When the agent calls it,
 * an interactive checklist overlay opens. The user can mark each test
 * as pass, fail (with error notes), or skip. Results are saved as
 * structured JSON to tests/uat/ and returned to the agent so it can
 * fix any failures.
 */

import type { ExtensionAPI } from "@mariozechner/pi-coding-agent";
import { Type } from "typebox";
import { Text } from "@mariozechner/pi-tui";
import { mkdir, writeFile, readFile } from "node:fs/promises";
import { join, resolve } from "node:path";

import { createChecklist, type TestItem, type UatResult } from "./checklist";

// ── Schema ─────────────────────────────────────────────────────────

const TestItemSchema = Type.Object({
  id: Type.String({ description: "Unique identifier for this test (e.g. '1', 'T1')" }),
  category: Type.String({ description: "Grouping category, e.g. 'Unauthenticated Access'" }),
  description: Type.String({ description: "What to test, e.g. '/map/ redirects to login'" }),
  expected_result: Type.Optional(
    Type.String({ description: "What should happen, e.g. '302 → /accounts/login/?next=/map/'" })
  ),
});

const UatParams = Type.Object({
  feature_name: Type.String({
    description:
      "Slug matching the UAT scenario file, e.g. 'reopen_completed_tasks' for tests/uat/reopen_completed_tasks_uat.md",
  }),
  test_items: Type.Array(TestItemSchema, {
    description: "All UAT test items the user should verify",
  }),
});

// ── Extension ──────────────────────────────────────────────────────

export default function uatChecklist(pi: ExtensionAPI) {
  pi.registerTool({
    name: "present_uat_tests",
    label: "UAT Tests",
    description:
      "Present an interactive UAT test checklist to the user. Use it to run a feature's UAT scenarios (from tests/uat/*.md). The user can mark each test as pass, fail (with an error note), or skip. Results are saved to tests/uat/<feature>-uat-results.json and failed tests are reported back so you can fix them.",
    promptSnippet: "Present interactive UAT test checklist for the user to verify",
    promptGuidelines: [
      "Call present_uat_tests with feature_name matching the UAT scenario file slug (e.g. tests/uat/reopen_completed_tasks_uat.md → 'reopen_completed_tasks') and all test items from that file so the user can verify interactively. When results return, immediately fix any failures the user reported.",
    ],
    parameters: UatParams,

    async execute(_toolCallId, params, _signal, _onUpdate, ctx) {
      if (!ctx.hasUI) {
        return {
          content: [
            {
              type: "text" as const,
              text: "Error: UAT checklist requires interactive mode. Tests cannot be verified non-interactively.",
            },
          ],
          details: {},
        };
      }

      const { feature_name, test_items } = params;
      const items: TestItem[] = test_items;

      if (items.length === 0) {
        return {
          content: [{ type: "text" as const, text: "No test items provided." }],
          details: {},
        };
      }

      // ── Load previous results if they exist ──
      const resultsDir = resolve(ctx.cwd, "tests", "uat");
      const resultsPath = join(resultsDir, `${feature_name}-uat-results.json`);

      let previousResults: UatResult | undefined;
      try {
        const existing = await readFile(resultsPath, "utf-8");
        previousResults = JSON.parse(existing) as UatResult;
      } catch {
        previousResults = undefined;
      }

      // ── Open interactive overlay ──
      const result = await ctx.ui.custom<UatResult>(
        (tui, theme, keybindings, done) => {
          return createChecklist(
            feature_name,
            items,
            {
              onDone: done,
              theme: theme as {
                fg: (color: string, text: string) => string;
                bg: (color: string, text: string) => string;
                bold: (text: string) => string;
              },
              keybindings,
            },
            tui,
            previousResults
          );
        },
        { overlay: true, overlayOptions: { maxHeight: "90%", width: "90%", minWidth: 60 } }
      );

      // ── Save results to file ──
      try {
        await mkdir(resultsDir, { recursive: true });
        await writeFile(resultsPath, JSON.stringify(result, null, 2), "utf-8");
      } catch (err) {
        // Log but don't block — results still go back to the agent
        console.error(`Failed to write UAT results: ${err}`);
      }

      // ── Format output for the agent ──
      const s = result.summary;
      const header = result.cancelled
        ? `UAT cancelled by user. ${s.passed} passed, ${s.failed} failed, ${s.pending} not checked.`
        : `UAT complete. ${s.total} tests: ${s.passed} passed, ${s.failed} failed, ${s.skipped} skipped, ${s.pending} pending.`;

      const lines: string[] = [header];

      if (!result.cancelled && s.failed > 0) {
        lines.push("\nFailed tests:");
        for (const item of result.items) {
          if (item.result === "fail") {
            const errMsg = item.error || "(no error message)";
            lines.push(`  ✗ [${item.category}] ${item.description} — ${errMsg}`);
          }
        }
        lines.push(`\nResults saved to: ${resultsPath}`);
      }

      const commented = result.items.filter((i) => i.comment);
      if (!result.cancelled && commented.length > 0) {
        lines.push("\nNotes:");
        for (const item of commented) {
          lines.push(`  • [${item.category}] ${item.description} — ${item.comment}`);
        }
      }

      if (!result.cancelled && s.pending > 0) {
        lines.push(
          `\n⚠ ${s.pending} test(s) not checked. These should be verified before sign-off.`
        );
      }

      if (result.cancelled) {
        lines.push(`\nPartial results saved to: ${resultsPath}`);
      }

      return {
        content: [{ type: "text" as const, text: lines.join("\n") }],
        details: result,
      };
    },

    // ── Custom rendering in tool output ──
    renderCall(args, theme, _context) {
      const feature = (args.feature_name as string) || "unknown";
      const count = (args.test_items as TestItem[] | undefined)?.length ?? 0;
      let text = theme.fg("toolTitle", theme.bold("uat_tests "));
      text += theme.fg("muted", `${count} test${count !== 1 ? "s" : ""}`);
      text += theme.fg("dim", ` for ${feature}`);
      return new Text(text, 0, 0);
    },

    renderResult(result, _options, theme, _context) {
      const details = result.details as UatResult | undefined;
      if (!details) {
        const first = result.content?.[0];
        return new Text(first?.type === "text" ? first.text : "", 0, 0);
      }

      if (details.cancelled) {
        return new Text(theme.fg("warning", "UAT cancelled"), 0, 0);
      }

      const s = details.summary;
      const lines: string[] = [];
      lines.push(
        `${theme.fg("success", `${s.passed} passed`)}  ` +
          (s.failed > 0
            ? theme.fg("error", `${s.failed} failed`)
            : theme.fg("dim", "0 failed")) +
          "  " +
          (s.skipped > 0
            ? theme.fg("warning", `${s.skipped} skipped`)
            : theme.fg("dim", "0 skipped")) +
          "  " +
          (s.pending > 0
            ? theme.fg("dim", `${s.pending} pending`)
            : theme.fg("dim", "all done"))
      );

      if (s.failed > 0) {
        lines.push("");
        lines.push(theme.fg("error", "Failed:"));
        for (const item of details.items) {
          if (item.result === "fail") {
            lines.push(
              `${theme.fg("error", "  ✗ ")}${theme.fg("text", item.description)}`
            );
            if (item.error) {
              lines.push(`    ${theme.fg("dim", item.error)}`);
            }
          }
        }
      }

      return new Text(lines.join("\n"), 0, 0);
    },
  });
}
