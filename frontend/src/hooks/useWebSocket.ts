import { useEffect, useRef } from "react";

type Listener = (evt: { kind: string; symbol?: string; data?: Record<string, unknown> }) => void;

class WSSingleton {
  private ws: WebSocket | null = null;
  private listeners = new Set<Listener>();
  private subs = new Map<string, Set<string>>();
  private retry = 0;
  private connecting = false;

  ensureConnected() {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) return;
    if (this.connecting) return;
    this.connecting = true;
    const proto = location.protocol === "https:" ? "wss" : "ws";
    const ws = new WebSocket(`${proto}://${location.host}/ws`);
    this.ws = ws;
    ws.onopen = () => {
      this.connecting = false;
      this.retry = 0;
      this.resubscribe();
    };
    ws.onmessage = (e) => {
      try {
        const evt = JSON.parse(e.data);
        this.listeners.forEach((l) => l(evt));
      } catch {
        /* ignore */
      }
    };
    ws.onclose = () => {
      this.connecting = false;
      this.ws = null;
      const delay = Math.min(30_000, 500 * 2 ** this.retry) + Math.random() * 500;
      this.retry += 1;
      setTimeout(() => this.ensureConnected(), delay);
    };
    ws.onerror = () => {
      ws.close();
    };
  }

  private resubscribe() {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) return;
    const allSymbols = new Set<string>();
    const allKinds = new Set<string>();
    for (const [sym, kinds] of this.subs.entries()) {
      allSymbols.add(sym);
      kinds.forEach((k) => allKinds.add(k));
    }
    if (allSymbols.size === 0) return;
    this.ws.send(
      JSON.stringify({
        action: "subscribe",
        symbols: [...allSymbols],
        kinds: [...allKinds],
      })
    );
  }

  subscribe(symbols: string[], kinds: string[]) {
    for (const s of symbols) {
      if (!this.subs.has(s)) this.subs.set(s, new Set());
      kinds.forEach((k) => this.subs.get(s)!.add(k));
    }
    this.ensureConnected();
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ action: "subscribe", symbols, kinds }));
    }
  }

  addListener(l: Listener) {
    this.listeners.add(l);
    return () => this.listeners.delete(l);
  }
}

const singleton = new WSSingleton();

export function useStream(symbols: string[], kinds: string[], onEvent: Listener) {
  const ref = useRef(onEvent);
  ref.current = onEvent;
  useEffect(() => {
    if (symbols.length === 0) return;
    singleton.subscribe(symbols, kinds);
    const off = singleton.addListener((e) => ref.current(e));
    return () => {
      off();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [symbols.join(","), kinds.join(",")]);
}

export function getStream() {
  return singleton;
}
