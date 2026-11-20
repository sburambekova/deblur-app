/** Deblur parameters as the API takes them (backend/app/schemas/params.py). Lengths are in
 * preview pixels: the backend scales them for the full-size render. */

export type Kernel = 'motion' | 'defocus';
export type Method = 'tikhonov' | 'tv' | 'rl';

export interface DeblurParams {
  kernel: Kernel;
  length: number;
  angle: number;
  radius: number;
  method: Method;
  mu: number;
  penalty: 'L2' | 'H1';
  lam: number;
  iters: number;
}

// The backend's defaults.
export const DEFAULT_PARAMS: DeblurParams = {
  kernel: 'motion',
  length: 15,
  angle: 0,
  radius: 3,
  method: 'rl',
  mu: 0.01,
  penalty: 'L2',
  lam: 5e-4,
  iters: 80,
};

/** Each method has one slider, s from 0 to 1, that sets its own parameter. mu and lam span four
 * orders of magnitude, so they are on a log scale. Both ends stay inside the API's limits:
 * mu above 0.1 is refused (Tikhonov with L2 visibly darkens the image there). */
interface Strength {
  label: string;
  fromS: (s: number) => number;
  toS: (value: number) => number;
}

// Two significant digits: the third one makes no visible difference and only clutters the label.
const round2 = (x: number) => Number(x.toPrecision(2));

export const STRENGTH: Record<Method, Strength> = {
  tikhonov: {
    label: 'Smoothing (μ)',
    fromS: (s) => round2(10 ** (-5 + 4 * s)),
    toS: (mu) => (Math.log10(mu) + 5) / 4,
  },
  tv: {
    label: 'Smoothing (λ)',
    fromS: (s) => round2(10 ** (-5 + 3.5 * s)),
    toS: (lam) => (Math.log10(lam) + 5) / 3.5,
  },
  rl: {
    label: 'Iterations',
    fromS: (s) => Math.round(5 + 195 * s),
    toS: (iters) => (iters - 5) / 195,
  },
};

/** The value the method's slider controls. */
export function strengthValue(p: DeblurParams): number {
  return { tikhonov: p.mu, tv: p.lam, rl: p.iters }[p.method];
}

/** The change of parameters for slider position s of the current method. */
export function strengthPatch(method: Method, s: number): Partial<DeblurParams> {
  const value = STRENGTH[method].fromS(s);
  return { tikhonov: { mu: value }, tv: { lam: value }, rl: { iters: value } }[method];
}

export function formatStrength(method: Method, value: number): string {
  if (method === 'rl') return String(value);
  return value >= 0.001 ? value.toFixed(3) : value.toExponential(1);
}

/** 15 -> "15", 2.5 -> "2.5", 17.123 -> "17.1" */
export const num = (x: number) => String(Number(x.toFixed(1)));

export function describeKernel(p: DeblurParams): string {
  return p.kernel === 'motion'
    ? `Motion blur, ${num(p.length)} px at ${num(p.angle)}°`
    : `Out of focus, radius ${num(p.radius)} px`;
}

export function describeMethod(p: DeblurParams): string {
  if (p.method === 'tikhonov') return `Fast (Tikhonov), μ ${formatStrength('tikhonov', p.mu)}`;
  if (p.method === 'tv') return `TV, λ ${formatStrength('tv', p.lam)}`;
  return `Richardson-Lucy, ${p.iters} iterations`;
}
