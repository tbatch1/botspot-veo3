// Simplified client-side logger (Winston only works server-side)

// Helpers to make errors readable in the browser console
function toPlainError(err: any) {
  if (!err) return err;
  const isAxios = err.isAxiosError || err.name === 'AxiosError';
  const base = {
    name: err.name,
    message: err.message,
    code: err.code,
  } as any;
  if (isAxios) {
    base.url = err.config?.url;
    base.method = err.config?.method;
    base.status = err.response?.status;
    base.statusText = err.response?.statusText;
    base.data = err.response?.data;
  }
  return base;
}

function safeFormat(arg: any): any {
  if (arg instanceof Error) return toPlainError(arg);
  try {
    // Avoid logging giant objects; stringify small plain objects
    if (arg && typeof arg === 'object') {
      return JSON.parse(JSON.stringify(arg));
    }
  } catch {}
  return arg;
}

function safeStringify(obj: any, maxLen = 4000): string {
  try {
    const cache = new Set<any>();
    const str = JSON.stringify(
      obj,
      (_k, v) => {
        if (typeof v === 'object' && v !== null) {
          if (cache.has(v)) return '[Circular]';
          cache.add(v);
        }
        if (typeof v === 'string' && v.length > 500) {
          return v.slice(0, 500) + '…';
        }
        return v;
      }
    );
    if (str.length > maxLen) return str.slice(0, maxLen) + '…';
    return str;
  } catch (e) {
    return String(obj);
  }
}

// Client-side logger with better error formatting
export const clientLogger = {
  info: (...args: any[]) => console.log('[INFO]', ...args.map(safeFormat)),
  debug: (...args: any[]) => console.debug('[DEBUG]', ...args.map(safeFormat)),
  warn: (...args: any[]) => console.warn('[WARN]', ...args.map(safeFormat)),
  error: (...args: any[]) => {
    const formatted = args.map(safeFormat);
    // Build a single-line summary so Next.js overlay (which shows only first arg) includes details
    const summary = formatted
      .map((a) => (typeof a === 'string' ? a : safeStringify(a)))
      .join(' | ');
    console.error(`[ERROR] ${summary}`);
    // Print stack separately if present
    for (const a of args) {
      if (a instanceof Error && a.stack) {
        console.error('[ERROR:stack]', a.stack);
        break;
      }
    }
  },
};

// Export as default logger (use Winston on backend if needed)
export const log = clientLogger;
export const logger = clientLogger;
