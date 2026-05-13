import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ChatPanel } from "./ChatPanel";

function renderWithClient(ui: React.ReactElement) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}

describe("ChatPanel", () => {
  it("renders the analyze NVDA hint when no messages exist", () => {
    renderWithClient(<ChatPanel />);
    const hint = screen.getByText(/Analyze NVDA/i);
    expect(hint).toBeTruthy();
  });
});
