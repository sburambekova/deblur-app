import { describe, expect, it } from 'vitest';

import { SPECTRUM_SIZE, defocusRing, motionOverlay } from './spectrum';

const C = SPECTRUM_SIZE / 2;

describe('motionOverlay', () => {
  it('draws a horizontal line for 0 degrees', () => {
    const { line } = motionOverlay(16, 0);
    expect(line.y1).toBeCloseTo(C);
    expect(line.y2).toBeCloseTo(C);
  });

  it('turns counter-clockwise on screen, where y points down', () => {
    const { line } = motionOverlay(16, 90);
    // The end in the motion direction is above the centre.
    expect(line.x2).toBeCloseTo(C);
    expect(line.y2).toBeLessThan(C);
  });

  it('puts the first marks 1/length cycles per pixel from the centre', () => {
    const { marks } = motionOverlay(16, 0);
    const xs = marks.map((m) => (m.x1 + m.x2) / 2);
    // 256 spectrum pixels per cycle per pixel, so 256 / 16 = 16 from the centre.
    expect(xs).toContain(C + 16);
    expect(xs).toContain(C - 16);
    // Each mark is across the line, i.e. vertical here.
    expect(marks[0].x1).toBeCloseTo(marks[0].x2);
  });

  it('leaves out marks that would merge into a line', () => {
    expect(motionOverlay(60, 0).marks).toEqual([]);
  });
});

describe('defocusRing', () => {
  it('shrinks as the disk grows', () => {
    expect(defocusRing(3)).toBeCloseTo(52.0, 0);
    expect(defocusRing(6)).toBeCloseTo(defocusRing(3) / 2);
  });
});
