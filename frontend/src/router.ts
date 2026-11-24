import { useSyncExternalStore } from 'react';

/** Screens live in the URL hash (#/photo/<id>), so a reload or a shared link opens the same
 * screen, and the server needs no rules for it: it only ever serves index.html for "/". */
export type Route =
  | { name: 'home' }
  | { name: 'editor'; photoId: string; jobId: string | null }
  | { name: 'gallery'; itemId: string | null };

export const paths = {
  home: '#/',
  gallery: '#/gallery',
  galleryItem: (itemId: string) => `#/gallery/${itemId}`,
  photo: (photoId: string) => `#/photo/${photoId}`,
  job: (photoId: string, jobId: string) => `#/photo/${photoId}/job/${jobId}`,
};

export function parseRoute(hash: string): Route {
  const [first, id, jobWord, jobId] = hash.replace(/^#\/?/, '').split('/');
  if (first === 'gallery') return { name: 'gallery', itemId: id || null };
  if (first === 'photo' && id) {
    return { name: 'editor', photoId: id, jobId: jobWord === 'job' && jobId ? jobId : null };
  }
  return { name: 'home' };
}

function subscribe(onChange: () => void) {
  window.addEventListener('hashchange', onChange);
  return () => window.removeEventListener('hashchange', onChange);
}

export function useRoute(): Route {
  return parseRoute(useSyncExternalStore(subscribe, () => window.location.hash));
}

/** Go to a path from `paths`. With replace, the browser's Back button skips the current screen. */
export function navigate(path: string, { replace = false } = {}) {
  if (!replace) {
    window.location.hash = path;
    return;
  }
  history.replaceState(null, '', path);
  // replaceState does not fire hashchange, so tell useRoute ourselves.
  window.dispatchEvent(new HashChangeEvent('hashchange'));
}
