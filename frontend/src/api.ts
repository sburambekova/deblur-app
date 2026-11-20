/** Calls to the backend. Vite (in development) and nginx (in production) pass /api and /files on
 * to the backend, so every path here is relative to the page. Types follow backend/app/schemas. */

import type { DeblurParams } from './params';

export interface Photo {
  id: string;
  width: number;
  height: number;
  preview_width: number;
  preview_height: number;
  full_url: string;
  preview_url: string;
  spectrum_url: string;
  created_at: string;
}

export interface Job {
  id: string;
  photo_id: string;
  status: 'queued' | 'running' | 'done' | 'failed';
  params: DeblurParams;
  result_url: string | null;
  error: string | null;
  created_at: string;
  started_at: string | null;
  finished_at: string | null;
  seconds: number | null;
}

export interface GalleryItem {
  id: string;
  job_id: string;
  photo_id: string;
  before_url: string;
  after_url: string;
  caption: string | null;
  params: DeblurParams;
  created_at: string;
}

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

/** fetch that throws ApiError with a message for the user when the request fails. */
async function send(path: string, init?: RequestInit): Promise<Response> {
  let res: Response;
  try {
    res = await fetch(path, init);
  } catch (err) {
    // An abort is the caller's own doing, not an error to show.
    if (init?.signal?.aborted) throw err;
    throw new ApiError(0, 'Cannot reach the server. Check the connection and try again.');
  }
  if (!res.ok) throw new ApiError(res.status, await errorMessage(res));
  return res;
}

async function errorMessage(res: Response): Promise<string> {
  if (res.status === 429) return 'The server is busy with other photos. Try again in a minute.';
  try {
    const { detail } = (await res.json()) as { detail?: unknown };
    if (typeof detail === 'string') return detail.endsWith('.') ? detail : `${detail}.`;
  } catch {
    // Not JSON: nginx answers a too large upload with its own HTML page.
  }
  if (res.status === 413) return 'This photo is too large. Try a smaller one.';
  return `Something went wrong (error ${res.status}). Try again.`;
}

export function messageOf(err: unknown): string {
  return err instanceof Error ? err.message : 'Something went wrong. Try again.';
}

const asJson = (params: DeblurParams, signal?: AbortSignal): RequestInit => ({
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(params),
  signal,
});

export async function uploadPhoto(file: Blob, name: string): Promise<Photo> {
  const form = new FormData();
  form.append('file', file, name);
  return (await send('/api/photos', { method: 'POST', body: form })).json();
}

export async function getPhoto(id: string, signal?: AbortSignal): Promise<Photo> {
  return (await send(`/api/photos/${id}`, { signal })).json();
}

/** Tikhonov preview at preview size, and the server time it took in ms. */
export async function fetchPreview(
  photoId: string,
  params: DeblurParams,
  signal: AbortSignal,
): Promise<{ blob: Blob; ms: number }> {
  const res = await send(`/api/photos/${photoId}/preview`, asJson(params, signal));
  return { blob: await res.blob(), ms: Number(res.headers.get('X-Compute-Ms')) };
}

export async function startRender(photoId: string, params: DeblurParams): Promise<Job> {
  return (await send(`/api/photos/${photoId}/render`, asJson(params))).json();
}

export async function getJob(id: string, signal?: AbortSignal): Promise<Job> {
  return (await send(`/api/jobs/${id}`, { signal })).json();
}

export async function listGallery(signal?: AbortSignal): Promise<GalleryItem[]> {
  return (await send('/api/gallery', { signal })).json();
}

export async function addToGallery(jobId: string, caption: string | null): Promise<GalleryItem> {
  const res = await send('/api/gallery', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ job_id: jobId, caption }),
  });
  return res.json();
}

export async function removeFromGallery(id: string): Promise<void> {
  await send(`/api/gallery/${id}`, { method: 'DELETE' });
}
