/**
 * Centralized test IDs for E2E testing with Playwright
 *
 * Usage:
 *   import { TID } from '@/testids';
 *   <div data-testid={TID.Chat.Answer}>...</div>
 *
 * Benefits:
 * - Type-safe test selectors
 * - Single source of truth
 * - Easy refactoring
 * - No more "selector whack-a-mole"
 */

export const TID = {
  Chat: {
    Form: "chat-form",
    Input: "chat-input",
    Send: "chat-send",
    Answer: "chat-answer",
    PerfBlock: "chat-perf",
    Sources: "chat-sources",
    SourceItem: (i: number) => `chat-source-${i}`,
  },
  Upload: {
    Zone: "upload-zone",
    Input: "upload-input",
    Item: (name: string) => `upload-item-${name}`,
    Error: "upload-error",
    List: "upload-list",
  },
  Research: {
    Panel: "research-panel",
    Run: "research-run",
    Status: "research-status",
    Error: "research-error",
    Results: "research-results",
  },
  Metrics: {
    Panel: "metrics-panel",
    TraceId: "metrics-trace-id",
    Tokens: "metrics-tokens",
    Cost: "metrics-cost",
    Latency: "metrics-latency",
  },
  Monitoring: {
    Panel: "monitoring-panel",
    CpuChart: "monitoring-cpu",
    GpuChart: "monitoring-gpu",
    HealthChart: "monitoring-health",
  },
} as const;

