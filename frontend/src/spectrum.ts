/** Where a kernel should leave its marks in the photo's spectrum, drawn over spectrum.png.
 *
 * spectrum.png is 256 x 256 with zero frequency in the centre and spans one cycle per preview
 * pixel across and down (the backend stretches it to a square, so angles stay true). A feature
 * at f cycles per pixel therefore lies f * 256 spectrum pixels from the centre. Lengths and
 * radii are in preview pixels, the same as the spectrum's. */

export const SPECTRUM_SIZE = 256;
const C = SPECTRUM_SIZE / 2;
const MARK_HALF = 7;
// Marks closer than this would merge into a solid line.
const MIN_MARK_STEP = 6;

export interface Segment {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
}

/** Motion blur: a line through the centre along the motion, and marks where the dark stripes
 * should cross it. The kernel's spectrum is zero every 1/length cycles per pixel along the
 * motion, so with the right length the marks sit on the stripes. */
export function motionOverlay(length: number, angle: number): { line: Segment; marks: Segment[] } {
  const a = (angle * Math.PI) / 180;
  // Counter-clockwise on screen, where y points down.
  const dx = Math.cos(a);
  const dy = -Math.sin(a);
  const reach = C * Math.SQRT2;
  const line = { x1: C - dx * reach, y1: C - dy * reach, x2: C + dx * reach, y2: C + dy * reach };

  const step = SPECTRUM_SIZE / length;
  const marks: Segment[] = [];
  if (step >= MIN_MARK_STEP) {
    for (let d = step; d < reach; d += step) {
      for (const side of [1, -1]) {
        const x = C + side * d * dx;
        const y = C + side * d * dy;
        // Across the line: the normal of (dx, dy) is (-dy, dx).
        marks.push({
          x1: x + dy * MARK_HALF,
          y1: y - dx * MARK_HALF,
          x2: x - dy * MARK_HALF,
          y2: y + dx * MARK_HALF,
        });
      }
    }
  }
  return { line, marks };
}

/** Defocus: radius of the first dark ring. A uniform disk of radius r has its first zero at
 * 0.61 / r cycles per pixel (the first zero of the Bessel function J1, 3.83, over 2 pi). */
export function defocusRing(radius: number): number {
  return (0.6098 / radius) * SPECTRUM_SIZE;
}
