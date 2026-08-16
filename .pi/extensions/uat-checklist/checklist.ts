/**
 * UAT Checklist — Interactive overlay component
 *
 * Renders a keyboard-driven checklist where users can mark test items
 * as pass, fail (with error notes), or skip. Results are returned to
 * the calling tool when the user presses Escape.
 */

import {
  type KeybindingsManager,
  decodeKittyPrintable,
  Key,
  matchesKey,
  truncateToWidth,
  type TUI,
} from "@mariozechner/pi-tui";

// ── Types ──────────────────────────────────────────────────────────

export interface TestItem {
  id: string;
  category: string;
  description: string;
  expected_result?: string;
}

export type ItemResult = "pending" | "pass" | "fail" | "skip";

export interface TestItemState extends TestItem {
  result: ItemResult;
  error?: string; // Only present when result === "fail"
  comment?: string; // General observation / note (any result)
}

export interface UatResult {
  feature: string;
  timestamp: string;
  summary: {
    total: number;
    passed: number;
    failed: number;
    skipped: number;
    pending: number;
  };
  items: TestItemState[];
  cancelled: boolean;
}

// ── Component ──────────────────────────────────────────────────────

export interface ChecklistCallbacks {
  onDone: (result: UatResult) => void;
  theme: {
    fg: (color: string, text: string) => string;
    bg: (color: string, text: string) => string;
    bold: (text: string) => string;
    dim?: (text: string) => string;
  };
  keybindings: KeybindingsManager;
}

/**
 * Creates a checklist component compatible with ctx.ui.custom().
 *
 * Returns an object with render(), handleInput(), and invalidate().
 */
export function createChecklist(
  feature: string,
  items: TestItem[],
  callbacks: ChecklistCallbacks,
  tui: TUI,
  previousResults?: UatResult
) {
  const { onDone, theme } = callbacks;

  // ── State ──
  const state: TestItemState[] = items.map((item) => {
    const prev = previousResults?.items.find((p) => p.id === item.id);
    if (prev) {
      return {
        ...item,
        result: prev.result,
        error: prev.error,
        comment: prev.comment,
      };
    }
    return {
      ...item,
      result: "pending" as ItemResult,
    };
  });

  let selectedIndex = 0;
  let inputMode: false | "error" | "comment" = false;
  let buffer = "";
  let cachedLines: string[] | undefined;
  let cachedWidth: number | undefined;
  let scrollOffset = 0;

  const t = theme;
  const bold = (s: string) => (t.bold ? t.bold(s) : s);

  // ── Helpers ──

  function clampIndex() {
    if (state.length === 0) return;
    if (selectedIndex < 0) selectedIndex = 0;
    if (selectedIndex >= state.length) selectedIndex = state.length - 1;
  }

  function invalidate() {
    cachedLines = undefined;
    cachedWidth = undefined;
    tui.requestRender();
  }

  function computeSummary() {
    const total = state.length;
    const passed = state.filter((s) => s.result === "pass").length;
    const failed = state.filter((s) => s.result === "fail").length;
    const skipped = state.filter((s) => s.result === "skip").length;
    const pending = total - passed - failed - skipped;
    return { total, passed, failed, skipped, pending };
  }

  function buildResult(cancelled: boolean): UatResult {
    return {
      feature,
      timestamp: new Date().toISOString(),
      summary: computeSummary(),
      items: state.map((s) => ({ ...s })),
      cancelled,
    };
  }

  // ── Keyboard ──

  function handleInput(data: string) {
    // Input mode: typing an error note or comment
    if (inputMode) {
      if (matchesKey(data, Key.escape)) {
        if (inputMode === "error") {
          // Cancel error input — revert to pending
          state[selectedIndex].result = "pending";
          state[selectedIndex].error = undefined;
        }
        // Comment mode: just discard changes
        inputMode = false;
        buffer = "";
        invalidate();
        return;
      }
      if (matchesKey(data, Key.enter)) {
        if (inputMode === "error") {
          state[selectedIndex].error = buffer.trim() || "(no message)";
        } else {
          const trimmed = buffer.trim();
          state[selectedIndex].comment = trimmed || undefined;
        }
        inputMode = false;
        buffer = "";
        invalidate();
        return;
      }
      if (matchesKey(data, Key.backspace)) {
        buffer = buffer.slice(0, -1);
        invalidate();
        return;
      }
      // Printable characters: try Kitty/decode first, fall back to raw char
      const decoded = decodeKittyPrintable(data);
      if (decoded !== undefined) {
        buffer += decoded;
        invalidate();
      } else if (data.length === 1 && data.charCodeAt(0) >= 32) {
        buffer += data;
        invalidate();
      }
      return;
    }

    // Navigation mode
    if (matchesKey(data, Key.up)) {
      selectedIndex--;
      clampIndex();
      invalidate();
      return;
    }
    if (matchesKey(data, Key.down)) {
      selectedIndex++;
      clampIndex();
      invalidate();
      return;
    }

    // Toggle pass (Enter or Space)
    if (matchesKey(data, Key.enter) || matchesKey(data, Key.space)) {
      const current = state[selectedIndex];
      current.result = current.result === "pass" ? "pending" : "pass";
      current.error = undefined;
      invalidate();
      return;
    }

    // Mark fail — enter error input mode
    if (matchesKey(data, "f") || matchesKey(data, "F")) {
      state[selectedIndex].result = "fail";
      state[selectedIndex].error = undefined;
      inputMode = "error";
      buffer = "";
      invalidate();
      return;
    }

    // Add / edit comment — enter comment input mode
    if (matchesKey(data, "c") || matchesKey(data, "C")) {
      inputMode = "comment";
      buffer = state[selectedIndex].comment || "";
      invalidate();
      return;
    }

    // Toggle skip
    if (matchesKey(data, "s") || matchesKey(data, "S")) {
      const current = state[selectedIndex];
      current.result = current.result === "skip" ? "pending" : "skip";
      current.error = undefined;
      invalidate();
      return;
    }

    // Done
    if (matchesKey(data, Key.escape)) {
      onDone(buildResult(false));
      return;
    }
  }

  // ── Render ──

  function render(width: number): string[] {
    if (cachedLines && cachedWidth === width) return cachedLines;
    cachedWidth = width;

    const lines: string[] = [];
    const add = (s: string) => lines.push(truncateToWidth(s, width));
    const summary = computeSummary();

    // ── Header ──
    add(t.fg("accent", "─".repeat(width)));
    add(bold(t.fg("text", ` UAT Checklist: ${feature}`)));
    add(
      t.fg("dim", ` ${summary.total} tests  ·  `) +
        t.fg("success", `${summary.passed} passed`) +
        t.fg("dim", "  ·  ") +
        (summary.failed > 0 ? t.fg("error", `${summary.failed} failed`) : t.fg("dim", "0 failed")) +
        t.fg("dim", "  ·  ") +
        (summary.skipped > 0 ? t.fg("warning", `${summary.skipped} skipped`) : t.fg("dim", "0 skipped")) +
        (summary.pending > 0 ? t.fg("dim", `  ·  ${summary.pending} pending`) : "")
    );
    add(t.fg("accent", "─".repeat(width)));

    if (state.length === 0) {
      lines.push("");
      add(t.fg("dim", " No test items to display."));
      lines.push("");
      add(t.fg("accent", "─".repeat(width)));
      cachedLines = lines;
      return lines;
    }

    // ── Build item lines (scrollable) ──
    const itemLines: string[] = [];
    const itemStartLines: number[] = [];
    let lastCategory = "";

    for (let i = 0; i < state.length; i++) {
      const item = state[i];
      const isSelected = i === selectedIndex;

      itemStartLines.push(itemLines.length);

      // Category header
      if (item.category !== lastCategory) {
        lastCategory = item.category;
        if (i > 0) {
          itemLines.push("");
        }
        itemLines.push(truncateToWidth(` ${t.fg("accent", bold(item.category))}`, width));
      }

      // Status indicator
      let indicator: string;
      switch (item.result) {
        case "pass":
          indicator = t.fg("success", " ✓ ");
          break;
        case "fail":
          indicator = t.fg("error", " ✗ ");
          break;
        case "skip":
          indicator = t.fg("warning", " ⊘ ");
          break;
        default:
          indicator = t.fg("dim", " ☐ ");
      }

      // Selection highlight
      const descColor = isSelected && !inputMode ? "selectedBg" : undefined;
      const descText = descColor
        ? t.bg(descColor, t.fg("text", item.description))
        : t.fg("text", item.description);

      itemLines.push(truncateToWidth(` ${indicator}${descText}`, width));

      // Expected result
      if (item.expected_result) {
        const expColor = isSelected && !inputMode ? "selectedBg" : undefined;
        const expText = expColor
          ? t.bg(expColor, t.fg("dim", `   → ${item.expected_result}`))
          : t.fg("dim", `   → ${item.expected_result}`);
        itemLines.push(truncateToWidth(expText, width));
      }

      // General comment (any result)
      if (item.comment) {
        itemLines.push(truncateToWidth(`      ${t.fg("dim", `Note: ${item.comment}`)}`, width));
      }

      // Error note for failed items
      if (item.result === "fail" && item.error) {
        const errColor = "error";
        itemLines.push(truncateToWidth(`      ${t.fg(errColor, `Error: ${item.error}`)}`, width));
      }
    }

    // ── Viewport: scroll items ──
    // Reserve space for header (~4), footer (~4), input mode (~4), and scroll indicators (~2)
    const fixedLines = 10 + (inputMode ? 4 : 0);
    const maxContentLines = Math.max(3, Math.floor(tui.terminal.rows * 0.9) - fixedLines);

    if (selectedIndex >= 0 && selectedIndex < state.length) {
      const selectedStart = itemStartLines[selectedIndex] ?? 0;
      const selectedEnd =
        selectedIndex < state.length - 1
          ? (itemStartLines[selectedIndex + 1] ?? itemLines.length)
          : itemLines.length;

      if (selectedStart < scrollOffset) {
        scrollOffset = selectedStart;
      } else if (selectedEnd > scrollOffset + maxContentLines) {
        scrollOffset = Math.max(0, selectedEnd - maxContentLines);
      }
    }

    const hasMoreAbove = scrollOffset > 0;
    const hasMoreBelow = scrollOffset + maxContentLines < itemLines.length;

    if (hasMoreAbove) {
      add(` ${t.fg("accent", `▲ ${scrollOffset} lines above`)}`);
    }

    for (let i = scrollOffset; i < Math.min(itemLines.length, scrollOffset + maxContentLines); i++) {
      lines.push(itemLines[i]!);
    }

    if (hasMoreBelow) {
      add(` ${t.fg("accent", `▼ ${itemLines.length - scrollOffset - maxContentLines} lines below`)}`);
    }

    // ── Input mode bar ──
    if (inputMode) {
      lines.push("");
      add(t.fg("accent", "─".repeat(width)));
      const prompt =
        inputMode === "error"
          ? t.fg("warning", " Describe the failure: ")
          : t.fg("accent", " Add a comment: ");
      const hint =
        inputMode === "error"
          ? " Enter to confirm  ·  Esc to cancel (reverts to pending)"
          : " Enter to confirm  ·  Esc to cancel";
      add(prompt + t.fg("text", buffer) + t.fg("dim", buffer.length === 0 ? "_" : ""));
      add(t.fg("dim", hint));
    }

    // ── Footer ──
    lines.push("");
    add(t.fg("accent", "─".repeat(width)));
    const pctDone = summary.total > 0 ? Math.round(((summary.passed + summary.failed + summary.skipped) / summary.total) * 100) : 0;
    add(
      t.fg("dim", ` ${pctDone}% checked  ·  `) +
        t.fg("dim", "Enter: pass  ·  ") +
        t.fg("dim", "F: fail  ·  ") +
        t.fg("dim", "S: skip  ·  ") +
        t.fg("dim", "C: comment  ·  ") +
        t.fg("dim", "↑↓: navigate  ·  ") +
        t.fg("accent", "Esc: done")
    );
    add(t.fg("accent", "─".repeat(width)));

    cachedLines = lines;
    return lines;
  }

  return {
    render,
    handleInput,
    invalidate,
  };
}
