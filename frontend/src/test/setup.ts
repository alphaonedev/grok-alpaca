import "@testing-library/react";

// jsdom doesn't implement Element.scrollTo — stub it for components that auto-scroll.
if (typeof Element !== "undefined" && !(Element.prototype as unknown as { scrollTo?: unknown }).scrollTo) {
  (Element.prototype as unknown as { scrollTo: () => void }).scrollTo = () => {};
}

// ResizeObserver is used by Plotly-based components; jsdom doesn't ship one.
if (typeof globalThis.ResizeObserver === "undefined") {
  class RO {
    observe() {}
    unobserve() {}
    disconnect() {}
  }
  (globalThis as unknown as { ResizeObserver: typeof RO }).ResizeObserver = RO;
}
