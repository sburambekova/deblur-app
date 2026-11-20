import { useRef, useState, type CSSProperties, type KeyboardEvent, type ReactNode } from 'react';

import { Arrows } from './icons';

interface Props {
  before: string;
  after: string;
  beforeAlt: string;
  afterAlt: string;
  /** Width / height of the photo; the frame keeps it, the photo is never cropped. */
  aspect: number;
  children?: ReactNode;
}

const clamp = (x: number) => Math.min(100, Math.max(0, x));

/** Before on the left, after on the right, with a divider to drag (or move with arrow keys). */
export function Compare({ before, after, beforeAlt, afterAlt, aspect, children }: Props) {
  const [pos, setPos] = useState(50);
  const frame = useRef<HTMLDivElement>(null);
  const dragging = useRef(false);

  function moveTo(clientX: number) {
    const rect = frame.current?.getBoundingClientRect();
    if (rect) setPos(clamp(((clientX - rect.left) / rect.width) * 100));
  }

  function onKeyDown(e: KeyboardEvent) {
    const next = { ArrowLeft: pos - 5, ArrowRight: pos + 5, Home: 0, End: 100 }[e.key];
    if (next === undefined) return;
    e.preventDefault();
    setPos(clamp(next));
  }

  return (
    <div
      ref={frame}
      className="compare"
      style={{ aspectRatio: aspect, '--aspect': aspect } as CSSProperties}
      onPointerDown={(e) => {
        dragging.current = true;
        e.currentTarget.setPointerCapture(e.pointerId);
        moveTo(e.clientX);
      }}
      onPointerMove={(e) => dragging.current && moveTo(e.clientX)}
      onPointerUp={() => (dragging.current = false)}
      onPointerCancel={() => (dragging.current = false)}
    >
      <img className="compare__img" src={after} alt={afterAlt} draggable={false} />
      <img
        className="compare__img"
        src={before}
        alt={beforeAlt}
        draggable={false}
        style={{ clipPath: `inset(0 ${100 - pos}% 0 0)` }}
      />
      <div className="compare__line" style={{ left: `${pos}%` }} />
      <div
        className="compare__handle"
        style={{ left: `${pos}%` }}
        role="slider"
        tabIndex={0}
        aria-label="Divider between before and after"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={Math.round(pos)}
        onKeyDown={onKeyDown}
      >
        <Arrows />
      </div>
      <span className="chip chip--bl">Before</span>
      <span className="chip chip--br">After</span>
      {children}
    </div>
  );
}
