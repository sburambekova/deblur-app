import { useEffect, useState, type CSSProperties } from 'react';

import {
  ApiError,
  addToGallery,
  getPhoto,
  messageOf,
  startRender,
  type Job,
  type Photo,
} from '../api';
import { Compare } from '../components/Compare';
import { KernelControls, MethodControls, Spectrum } from '../components/Controls';
import { Download } from '../components/icons';
import { BackLink, Brand, GalleryLink, TopBar } from '../components/TopBar';
import { useJob, useMediaQuery, usePreview, type Preview } from '../hooks';
import { DEFAULT_PARAMS, describeKernel, describeMethod, type DeblurParams } from '../params';
import { navigate, paths } from '../router';

const WIDE = '(min-width: 960px)';
const GONE =
  'This photo is no longer on the server. Photos are deleted after 24 hours unless they are saved to the gallery.';

const storageKey = (photoId: string) => `deblur:params:${photoId}`;

// The settings survive a reload, or a trip to the gallery and back, in the same tab.
function loadParams(photoId: string): DeblurParams {
  try {
    const saved = sessionStorage.getItem(storageKey(photoId));
    if (saved) return { ...DEFAULT_PARAMS, ...JSON.parse(saved) };
  } catch {
    // Storage may be blocked (private mode); the defaults will do.
  }
  return DEFAULT_PARAMS;
}

interface ViewProps {
  photo: Photo;
  params: DeblurParams;
  update: (patch: Partial<DeblurParams>) => void;
  preview: Preview | null;
  pending: boolean;
  jobId: string | null;
  job: Job | null;
  error: string | null;
  starting: boolean;
  sharpen: () => void;
}

/** Adjusting a photo and rendering it. On a phone these are two screens: a job in the URL
 * switches to the result. On a wide screen they are one. */
export function Editor({ photoId, jobId }: { photoId: string; jobId: string | null }) {
  const wide = useMediaQuery(WIDE);
  const [photo, setPhoto] = useState<Photo | null>(null);
  const [photoError, setPhotoError] = useState<string | null>(null);
  const [params, setParams] = useState(() => loadParams(photoId));
  const { preview, pending, error: previewError } = usePreview(photoId, params);
  const { job, error: jobError } = useJob(jobId);
  const [starting, setStarting] = useState(false);
  const [startError, setStartError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    getPhoto(photoId, controller.signal).then(setPhoto, (err) => {
      if (controller.signal.aborted) return;
      setPhotoError(err instanceof ApiError && err.status === 404 ? GONE : messageOf(err));
    });
    return () => controller.abort();
  }, [photoId]);

  useEffect(() => {
    try {
      sessionStorage.setItem(storageKey(photoId), JSON.stringify(params));
    } catch {
      // See loadParams.
    }
  }, [photoId, params]);

  function update(patch: Partial<DeblurParams>) {
    setParams((p) => ({ ...p, ...patch }));
    // The render on screen was made with the old settings: go back to the live preview.
    if (jobId) navigate(paths.photo(photoId), { replace: true });
  }

  async function sharpen() {
    setStarting(true);
    setStartError(null);
    try {
      const next = await startRender(photoId, params);
      // From one result to the next, Back should still lead to the settings.
      navigate(paths.job(photoId, next.id), { replace: jobId !== null });
    } catch (err) {
      setStartError(messageOf(err));
    } finally {
      setStarting(false);
    }
  }

  if (photoError) return <Gone message={photoError} />;
  if (!photo) {
    return (
      <div className="screen">
        <TopBar left={<BackLink href={paths.home} />} />
        <p className="lead" role="status">
          Loading…
        </p>
      </div>
    );
  }

  const view: ViewProps = {
    photo,
    params,
    update,
    preview,
    pending,
    jobId,
    job,
    error: startError ?? jobError ?? previewError,
    starting,
    sharpen,
  };
  if (wide) return <DesktopEditor {...view} />;
  return jobId ? <MobileResult {...view} /> : <MobileAdjust {...view} />;
}

function MobileAdjust(v: ViewProps) {
  return (
    <div className="screen screen--adjust">
      <TopBar left={<BackLink href={paths.home} />} title="Adjust" right={<GalleryLink />} />
      <PreviewStage {...v} working={false} />
      <KernelControls params={v.params} update={v.update} />
      <MethodControls params={v.params} update={v.update} />
      <div className="spacer" />
      <div className="sticky-bottom">
        {v.error && (
          <p className="error" role="alert">
            {v.error}
          </p>
        )}
        <button className="btn btn--primary" onClick={v.sharpen} disabled={v.starting}>
          Sharpen
        </button>
      </div>
    </div>
  );
}

function MobileResult(v: ViewProps) {
  const { photo, job } = v;
  const save = useSaveToGallery(job);
  const done = job?.status === 'done';
  const error = save.error ?? v.error;
  return (
    <div className="screen">
      <TopBar left={<BackLink href={paths.photo(photo.id)} />} title="Result" right={<GalleryLink />} />
      {done ? <ResultCompare photo={photo} job={job} /> : <JobStage photo={photo} job={job} />}
      <JobSummary photo={photo} job={job} />
      {done && <CaptionField value={save.caption} onChange={save.setCaption} />}
      <div className="spacer" />
      <div className="btn-stack">
        {error && (
          <p className="error" role="alert">
            {error}
          </p>
        )}
        {job?.status === 'failed' ? (
          <button className="btn btn--primary" onClick={v.sharpen} disabled={v.starting}>
            Try again
          </button>
        ) : (
          <>
            <a
              className="btn btn--primary"
              href={job?.result_url ?? undefined}
              download={job ? downloadName(job) : undefined}
              aria-disabled={!done}
            >
              <Download />
              Download
            </a>
            <button
              className="btn btn--secondary"
              onClick={save.save}
              disabled={!done || save.saving}
            >
              Save to gallery
            </button>
          </>
        )}
        <a className="btn btn--text" href={paths.home}>
          New photo
        </a>
      </div>
    </div>
  );
}

function DesktopEditor(v: ViewProps) {
  const { photo, params, update, job } = v;
  const save = useSaveToGallery(job);
  const done = job?.status === 'done';
  // Until the job has loaded it counts as running: it was started a moment ago.
  const working = v.jobId !== null && !done && job?.status !== 'failed';
  const error = save.error ?? v.error;
  return (
    <div className="desk">
      <TopBar
        left={<Brand />}
        right={
          <>
            <a className="link" href={paths.home}>
              New photo
            </a>
            <GalleryLink />
          </>
        }
      />
      <main className="desk__main">
        <div className="desk__stage">
          {done ? (
            <ResultCompare photo={photo} job={job} />
          ) : (
            <PreviewStage {...v} working={working} />
          )}
        </div>
        <aside className="desk__panel">
          <KernelControls params={params} update={update} />
          <Spectrum src={photo.spectrum_url} params={params} />
          <MethodControls params={params} update={update} />
          {job?.status === 'failed' && (
            <p className="error">The render failed on the server. Try again, or choose Fast.</p>
          )}
          {done && <CaptionField value={save.caption} onChange={save.setCaption} />}
          {error && (
            <p className="error" role="alert">
              {error}
            </p>
          )}
          <div className="btn-row">
            <button
              className="btn btn--primary"
              onClick={v.sharpen}
              disabled={v.starting || working}
            >
              {working ? 'Sharpening…' : 'Sharpen'}
            </button>
            <button
              className="btn btn--secondary"
              onClick={save.save}
              disabled={!done || save.saving}
            >
              Save to gallery
            </button>
          </div>
          {done && job.result_url && (
            <p className="note">
              {photo.width} × {photo.height} px, rendered in {job.seconds?.toFixed(1)} s ·{' '}
              <a className="link-inline" href={job.result_url} download={downloadName(job)}>
                Download JPEG
              </a>
            </p>
          )}
        </aside>
      </main>
    </div>
  );
}

/** The photo against the live preview, or a progress bar while a full render runs. */
function PreviewStage({ photo, preview, pending, working }: ViewProps & { working: boolean }) {
  let chip = 'Preview…';
  if (working) chip = 'Sharpening at full size…';
  else if (preview && !pending) chip = `Preview · ${Math.round(preview.ms)} ms`;
  return (
    <Compare
      before={photo.preview_url}
      after={preview?.url ?? photo.preview_url}
      beforeAlt="The photo as uploaded"
      afterAlt="Preview with the current settings"
      aspect={photo.preview_width / photo.preview_height}
    >
      <span className="chip chip--tl">{chip}</span>
      {working && <div className="progress progress--edge" role="status" aria-label={chip} />}
    </Compare>
  );
}

function ResultCompare({ photo, job }: { photo: Photo; job: Job }) {
  return (
    <Compare
      before={photo.full_url}
      after={job.result_url ?? ''}
      beforeAlt="The photo as uploaded"
      afterAlt="The sharpened photo"
      aspect={photo.width / photo.height}
    >
      <span className="chip chip--tl">Full size</span>
    </Compare>
  );
}

/** The photo with the job's status over it, while there is no result to compare. */
function JobStage({ photo, job }: { photo: Photo; job: Job | null }) {
  const failed = job?.status === 'failed';
  const aspect = photo.width / photo.height;
  let title = 'Sharpening…';
  if (job?.status === 'queued') title = 'Waiting in line…';
  if (failed) title = 'The render failed';
  return (
    <div className="stage" style={{ aspectRatio: aspect, '--aspect': aspect } as CSSProperties}>
      <img className="stage__img" src={photo.preview_url} alt="The photo being sharpened" />
      <div className="stage__status" role="status">
        <span>{title}</span>
        {!failed && <div className="progress" />}
      </div>
    </div>
  );
}

function JobSummary({ photo, job }: { photo: Photo; job: Job | null }) {
  if (!job) return null;
  if (job.status === 'failed') {
    return (
      <div className="summary">
        <p className="error">The render failed on the server. Try again, or choose Fast, which is much quicker.</p>
        {job.error && <p className="note">Server message: {job.error}</p>}
      </div>
    );
  }
  const size = `${photo.width} × ${photo.height} px`;
  return (
    <div className="summary">
      <p className="lead">
        {describeKernel(job.params)}. {describeMethod(job.params)}.
      </p>
      <p className="note">
        {job.status === 'done'
          ? `${size}, rendered in ${job.seconds?.toFixed(1)} s`
          : `Working on the full ${size} photo. This page updates by itself.`}
      </p>
    </div>
  );
}

function CaptionField({ value, onChange }: { value: string; onChange: (v: string) => void }) {
  return (
    <div className="field">
      <label htmlFor="caption">
        Caption <span className="muted">(optional)</span>
      </label>
      <input
        id="caption"
        className="input"
        maxLength={120}
        placeholder="What is in the photo?"
        value={value}
        onChange={(e) => onChange(e.target.value)}
      />
      <p className="note">The gallery is public: everyone who opens the site can see it.</p>
    </div>
  );
}

function Gone({ message }: { message: string }) {
  return (
    <div className="screen">
      <TopBar left={<BackLink href={paths.home} />} right={<GalleryLink />} />
      <h1 className="title">Photo not found</h1>
      <p className="lead">{message}</p>
      <div className="spacer" />
      <a className="btn btn--primary" href={paths.home}>
        New photo
      </a>
    </div>
  );
}

/** Saving is always an explicit action: the gallery is public and photos can be private. */
function useSaveToGallery(job: Job | null) {
  const [caption, setCaption] = useState('');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function save() {
    if (!job) return;
    setSaving(true);
    setError(null);
    try {
      await addToGallery(job.id, caption.trim() || null);
      navigate(paths.gallery);
    } catch (err) {
      setError(messageOf(err));
      setSaving(false);
    }
  }

  return { caption, setCaption, saving, error, save };
}

const downloadName = (job: Job) => `deblurred-${job.id.slice(0, 8)}.jpg`;
