import type { CSSProperties } from 'react';

interface SliderProps {
  id: string;
  label: string;
  value: number;
  min: number;
  max: number;
  step: number;
  /** The value as the user reads it, e.g. "15 px". */
  display: string;
  onChange: (value: number) => void;
}

export function Slider({ id, label, value, min, max, step, display, onChange }: SliderProps) {
  // How far the track is filled, 0..1; the CSS draws the fill from it.
  const fill = { '--fill': (value - min) / (max - min) } as CSSProperties;
  return (
    <div className="slider">
      <div className="slider__head">
        <label htmlFor={id}>{label}</label>
        <output htmlFor={id}>{display}</output>
      </div>
      <input
        id={id}
        className="range"
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        style={fill}
        onChange={(e) => onChange(Number(e.target.value))}
      />
    </div>
  );
}

interface SegmentedProps<T extends string> {
  label: string;
  options: { value: T; label: string }[];
  value: T;
  onChange: (value: T) => void;
}

export function Segmented<T extends string>({ label, options, value, onChange }: SegmentedProps<T>) {
  return (
    <div className="seg" role="group" aria-label={label}>
      {options.map((o) => (
        <button
          key={o.value}
          type="button"
          className="seg__btn"
          aria-pressed={o.value === value}
          onClick={() => onChange(o.value)}
        >
          {o.label}
        </button>
      ))}
    </div>
  );
}
