import '@testing-library/jest-dom';

// jsdom has no ResizeObserver; Radix components (e.g. Checkbox) call it on mount.
if (typeof globalThis.ResizeObserver === 'undefined') {
  globalThis.ResizeObserver = class {
    observe() {}
    unobserve() {}
    disconnect() {}
  } as unknown as typeof ResizeObserver;
}
