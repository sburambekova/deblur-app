import { describe, expect, it } from 'vitest';

import { parseRoute, paths } from './router';

describe('parseRoute', () => {
  it('reads every screen back from its path', () => {
    expect(parseRoute(paths.home)).toEqual({ name: 'home' });
    expect(parseRoute(paths.gallery)).toEqual({ name: 'gallery', itemId: null });
    expect(parseRoute(paths.galleryItem('g1'))).toEqual({ name: 'gallery', itemId: 'g1' });
    expect(parseRoute(paths.photo('abc'))).toEqual({ name: 'editor', photoId: 'abc', jobId: null });
    expect(parseRoute(paths.job('abc', 'j1'))).toEqual({ name: 'editor', photoId: 'abc', jobId: 'j1' });
  });

  it('falls back to home', () => {
    expect(parseRoute('')).toEqual({ name: 'home' });
    expect(parseRoute('#/nowhere')).toEqual({ name: 'home' });
    expect(parseRoute('#/photo/')).toEqual({ name: 'home' });
  });
});
