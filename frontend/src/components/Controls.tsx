import {
  STRENGTH,
  formatStrength,
  num,
  strengthPatch,
  strengthValue,
  type DeblurParams,
  type Kernel,
  type Method,
} from '../params';
import { SPECTRUM_SIZE, defocusRing, motionOverlay, type Segment } from '../spectrum';
import { Segmented, Slider } from './Inputs';

interface Props {
  params: DeblurParams;
  update: (patch: Partial<DeblurParams>) => void;
}

const KERNELS: { value: Kernel; label: string }[] = [
  { value: 'motion', label: 'Motion' },
  { value: 'defocus', label: 'Out of focus' },
];

const METHODS: { value: Method; label: string }[] = [
  { value: 'tikhonov', label: 'Fast' },
  { value: 'tv', label: 'TV' },
  { value: 'rl', label: 'R-L' },
];

/** Blur type and its size. Ranges are the API's (backend/app/schemas/params.py). */
export function KernelControls({ params, update }: Props) {
  return (
    <div className="controls">
      <Segmented
        label="Blur type"
        options={KERNELS}
        value={params.kernel}
        onChange={(kernel) => update({ kernel })}
      />
      {params.kernel === 'motion' ? (
        <>
          <Slider
            id="length"
            label="Blur length"
            min={1}
            max={60}
            step={1}
            value={params.length}
            display={`${num(params.length)} px`}
            onChange={(length) => update({ length })}
          />
          <Slider
            id="angle"
            label="Direction"
            min={0}
            max={180}
            step={1}
            value={params.angle}
            display={`${num(params.angle)}°`}
            onChange={(angle) => update({ angle })}
          />
        </>
      ) : (
        <Slider
          id="radius"
          label="Radius"
          min={0.5}
          max={25}
          step={0.5}
          value={params.radius}
          display={`${num(params.radius)} px`}
          onChange={(radius) => update({ radius })}
        />
      )}
    </div>
  );
}

/** Method of the full-size render and its one strength slider. */
export function MethodControls({ params, update }: Props) {
  const value = strengthValue(params);
  return (
    <div className="controls">
      <Segmented
        label="Method"
        options={METHODS}
        value={params.method}
        onChange={(method) => update({ method })}
      />
      <Slider
        id="strength"
        label={STRENGTH[params.method].label}
        min={0}
        max={1}
        step={0.005}
        value={STRENGTH[params.method].toS(value)}
        display={formatStrength(params.method, value)}
        onChange={(s) => update(strengthPatch(params.method, s))}
      />
      <p className="note">
        {params.method === 'tikhonov'
          ? 'The live preview uses Fast too. Sharpen runs it on the full photo.'
          : `The preview always uses Fast. ${params.method === 'tv' ? 'TV' : 'R-L'} runs on the full photo when you sharpen.`}
      </p>
    </div>
  );
}

function Line({ s }: { s: Segment }) {
  return (
    <>
      <line className="spectrum__halo" x1={s.x1} y1={s.y1} x2={s.x2} y2={s.y2} />
      <line className="spectrum__ink" x1={s.x1} y1={s.y1} x2={s.x2} y2={s.y2} />
    </>
  );
}

/** The photo's spectrum with the current kernel drawn over it, to line the two up by eye. */
export function Spectrum({ src, params }: { src: string; params: DeblurParams }) {
  const c = SPECTRUM_SIZE / 2;
  const motion = params.kernel === 'motion' ? motionOverlay(params.length, params.angle) : null;
  return (
    <figure className="spectrum">
      <div className="spectrum__frame">
        <img src={src} alt="" />
        <svg viewBox={`0 0 ${SPECTRUM_SIZE} ${SPECTRUM_SIZE}`} aria-hidden="true">
          {motion ? (
            <>
              <Line s={motion.line} />
              {motion.marks.map((m, i) => (
                <Line key={i} s={m} />
              ))}
            </>
          ) : (
            <>
              <circle className="spectrum__halo" cx={c} cy={c} r={defocusRing(params.radius)} />
              <circle className="spectrum__ink" cx={c} cy={c} r={defocusRing(params.radius)} />
            </>
          )}
        </svg>
      </div>
      <figcaption>
        {motion
          ? 'Spectrum of the photo. With the right direction the line crosses the dark stripes at a right angle, and with the right length the marks sit on them.'
          : 'Spectrum of the photo. With the right radius the circle sits on the first dark ring.'}
      </figcaption>
    </figure>
  );
}
