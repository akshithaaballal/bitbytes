// Simple helper to perform a fetch that can be aborted via AbortController.
// Returns an object {promise, abort} where promise resolves with JSON data.
export default function useAbortableFetch(url, options = {}) {
  const controller = new AbortController();
  const { signal, ...rest } = options;
  const fetchOptions = { ...rest, signal: controller.signal };
  const promise = fetch(url, fetchOptions).then((res) => {
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  });
  return { promise, abort: () => controller.abort() };
}
