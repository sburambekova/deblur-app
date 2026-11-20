import { useCallback, useEffect, useRef, useState, useSyncExternalStore } from 'react';

import { ApiError, fetchPreview, getJob, messageOf, type Job } from './api';
import { DEFAULT_PARAMS, type DeblurParams } from './params';

export function useMediaQuery(query: string): boolean {
  const subscribe = useCallback(
    (onChange: () => void) => {
      const list = window.matchMedia(query);
      list.addEventListener('change', onChange);
      return () => list.removeEventListener('change', onChange);
    },
    [query],
  );
  return useSyncExternalStore(subscribe, () => window.matchMedia(query).matches);
}

// Long enough to skip the positions a slider passes through while it is dragged, short enough
// that the preview still feels live. The preview itself takes about 40 ms on the server.
const PREVIEW_DELAY_MS = 120;

export interface Preview {
  url: string;
  ms: number;
}

/** Live Tikhonov preview for the current kernel. `pending` is true while it is out of date. */
export function usePreview(photoId: string, params: DeblurParams) {
  const [preview, setPreview] = useState<(Preview & { key: string }) | null>(null);
  const [error, setError] = useState<string | null>(null);
  const urlRef = useRef<string | null>(null);

  // Only these parameters change the preview: it is always Tikhonov, so switching the method or
  // its iterations must not send a request.
  const { kernel, length, angle, radius, mu, penalty } = params;
  const key = JSON.stringify([photoId, kernel, length, angle, radius, mu, penalty]);

  useEffect(() => {
    const controller = new AbortController();
    const timer = setTimeout(async () => {
      const previewParams = { ...DEFAULT_PARAMS, kernel, length, angle, radius, mu, penalty };
      try {
        const { blob, ms } = await fetchPreview(photoId, previewParams, controller.signal);
        if (urlRef.current) URL.revokeObjectURL(urlRef.current);
        urlRef.current = URL.createObjectURL(blob);
        setPreview({ url: urlRef.current, ms, key });
        setError(null);
      } catch (err) {
        if (!controller.signal.aborted) setError(messageOf(err));
      }
    }, PREVIEW_DELAY_MS);
    // A newer request replaces this one: aborting it means a slow old answer can never arrive
    // after a newer one and show the wrong settings.
    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, [key, photoId, kernel, length, angle, radius, mu, penalty]);

  useEffect(
    () => () => {
      if (urlRef.current) URL.revokeObjectURL(urlRef.current);
    },
    [],
  );

  return { preview, pending: preview?.key !== key, error };
}

const POLL_MS = 700;
const RETRY_MS = 3000;

/** The render job, polled until it is done or failed. */
export function useJob(jobId: string | null) {
  const [job, setJob] = useState<Job | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!jobId) return;
    const controller = new AbortController();
    let timer: ReturnType<typeof setTimeout>;
    const poll = async () => {
      try {
        const next = await getJob(jobId, controller.signal);
        setJob(next);
        setError(null);
        if (next.status === 'queued' || next.status === 'running') timer = setTimeout(poll, POLL_MS);
      } catch (err) {
        if (controller.signal.aborted) return;
        setError(messageOf(err));
        // A lost connection may come back; a job that does not exist will not.
        if (!(err instanceof ApiError && err.status === 404)) timer = setTimeout(poll, RETRY_MS);
      }
    };
    poll();
    return () => {
      controller.abort();
      clearTimeout(timer);
    };
  }, [jobId]);

  // After a switch to another job the old one may still be in state for a moment.
  return { job: job && job.id === jobId ? job : null, error: jobId ? error : null };
}
