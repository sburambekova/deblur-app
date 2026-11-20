import { describe, expect, it } from 'vitest';

import {
  DEFAULT_PARAMS,
  STRENGTH,
  describeKernel,
  describeMethod,
  formatStrength,
  strengthPatch,
  strengthValue,
  type Method,
} from './params';

const METHODS: Method[] = ['tikhonov', 'tv', 'rl'];

describe('strength slider', () => {
  // The API refuses values outside these (backend/app/schemas/params.py) with 422.
  it('stays inside the API limits at both ends', () => {
    for (const s of [0, 1]) {
      const { mu, lam, iters } = { ...strengthPatch('tikhonov', s), ...strengthPatch('tv', s), ...strengthPatch('rl', s) };
      expect(mu).toBeGreaterThanOrEqual(1e-6);
      expect(mu).toBeLessThanOrEqual(0.1);
      expect(lam).toBeGreaterThanOrEqual(1e-6);
      expect(lam).toBeLessThanOrEqual(0.1);
      expect(iters).toBeGreaterThanOrEqual(1);
      expect(iters).toBeLessThanOrEqual(200);
    }
  });

  it('puts the defaults inside the slider and maps them back', () => {
    for (const method of METHODS) {
      const params = { ...DEFAULT_PARAMS, method };
      const value = strengthValue(params);
      const s = STRENGTH[method].toS(value);
      expect(s).toBeGreaterThan(0);
      expect(s).toBeLessThan(1);
      const back = strengthValue({ ...params, ...strengthPatch(method, s) });
      expect(back).toBeCloseTo(value, 5);
    }
  });

  it('changes only the parameter of the method', () => {
    expect(strengthPatch('tikhonov', 0.75)).toEqual({ mu: 0.01 });
    expect(strengthPatch('rl', 0)).toEqual({ iters: 5 });
    expect(Object.keys(strengthPatch('tv', 0.5))).toEqual(['lam']);
  });
});

describe('labels', () => {
  it('formats strengths', () => {
    expect(formatStrength('tikhonov', 0.01)).toBe('0.010');
    expect(formatStrength('tv', 5e-4)).toBe('5.0e-4');
    expect(formatStrength('rl', 80)).toBe('80');
  });

  it('describes the parameters', () => {
    expect(describeKernel({ ...DEFAULT_PARAMS, length: 17.04, angle: 30 })).toBe('Motion blur, 17 px at 30°');
    expect(describeKernel({ ...DEFAULT_PARAMS, kernel: 'defocus', radius: 2.5 })).toBe('Out of focus, radius 2.5 px');
    expect(describeMethod(DEFAULT_PARAMS)).toBe('Richardson-Lucy, 80 iterations');
    expect(describeMethod({ ...DEFAULT_PARAMS, method: 'tikhonov' })).toBe('Fast (Tikhonov), μ 0.010');
  });
});
