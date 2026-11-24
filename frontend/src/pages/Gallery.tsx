import { useEffect, useRef, useState, type MouseEvent } from 'react';

import { listGallery, messageOf, removeFromGallery, type GalleryItem } from '../api';
import { Compare } from '../components/Compare';
import { ChevronLeft, ChevronRight, Close, Download, Trash } from '../components/icons';
import { BackLink, TopBar } from '../components/TopBar';
import { describeKernel, describeMethod } from '../params';
import { navigate, paths } from '../router';

const date = new Intl.DateTimeFormat('en', { day: 'numeric', month: 'short' });

/** The saved photos. With an item in the URL it is open on top, to look at but not to change. */
export function Gallery({ itemId }: { itemId: string | null }) {
  const [items, setItems] = useState<GalleryItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    listGallery(controller.signal).then(setItems, (err) => {
      if (!controller.signal.aborted) setError(messageOf(err));
    });
    return () => controller.abort();
  }, []);

  async function remove(item: GalleryItem) {
    // The gallery is shared, so a removal is gone for everyone.
    if (!window.confirm('Remove this photo from the gallery for everyone?')) return;
    setItems((list) => list && list.filter((i) => i.id !== item.id));
    try {
      await removeFromGallery(item.id);
    } catch (err) {
      setError(messageOf(err));
      listGallery().then(setItems, () => {});
    }
  }

  // An unknown id (a removed photo, an old link) just shows the gallery.
  const open = items?.findIndex((i) => i.id === itemId) ?? -1;

  return (
    <div className="screen screen--gallery">
      <TopBar left={<BackLink href={paths.home} label="Home" />} title="Gallery" />
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      {items === null && !error && (
        <p className="lead" role="status">
          Loading…
        </p>
      )}
      {items?.length === 0 && (
        <p className="empty">Nothing here yet. Sharpen a photo and tap Save to gallery.</p>
      )}
      {items && items.length > 0 && (
        <div className="gallery">
          {items.map((item) => (
            <GalleryCard key={item.id} item={item} onRemove={() => remove(item)} />
          ))}
        </div>
      )}
      <div className="spacer" />
      <div className="sticky-bottom">
        <a className="btn btn--primary" href={paths.home}>
          New photo
        </a>
      </div>
      {items && open >= 0 && <Viewer items={items} index={open} />}
    </div>
  );
}

/** Title and the line under it, the same on a card and in the viewer. */
function describe(item: GalleryItem) {
  const kernel = describeKernel(item.params);
  return {
    title: item.caption ?? kernel,
    meta: `${item.caption ? `${kernel} · ` : ''}${describeMethod(item.params)} · ${date.format(new Date(item.created_at))}`,
  };
}

function GalleryCard({ item, onRemove }: { item: GalleryItem; onRemove: () => void }) {
  const { title, meta } = describe(item);
  return (
    <article className="card">
      <a className="pair" href={paths.galleryItem(item.id)} aria-label={`Open: ${title}`}>
        <figure>
          <img src={item.before_url} alt="Before" loading="lazy" decoding="async" />
          <span className="chip chip--bl chip--sm">Before</span>
        </figure>
        <figure>
          <img src={item.after_url} alt="After" loading="lazy" decoding="async" />
          <span className="chip chip--bl chip--sm">After</span>
        </figure>
      </a>
      <div className="card__foot">
        <div className="card__text">
          <p className="card__title">{title}</p>
          <p className="card__meta">{meta}</p>
        </div>
        <button className="icon-btn" aria-label="Remove from gallery" onClick={onRemove}>
          <Trash />
        </button>
      </div>
    </article>
  );
}

/** One gallery photo over the page, with the before / after divider. The settings are only
 * shown as text: a saved result is not edited. */
function Viewer({ items, index }: { items: GalleryItem[]; index: number }) {
  const item = items[index];
  const { title, meta } = describe(item);
  const aspect = useAspect(item.after_url);
  const closeBtn = useRef<HTMLButtonElement>(null);

  // replace: stepping through photos does not fill the Back button's history.
  const close = () => navigate(paths.gallery, { replace: true });
  const go = (i: number) => {
    if (i >= 0 && i < items.length) navigate(paths.galleryItem(items[i].id), { replace: true });
  };

  useEffect(() => {
    closeBtn.current?.focus();
    // The page under the viewer stays where it was.
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = '';
    };
  }, []);

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      // The divider uses the arrow keys itself when it has focus, and marks them as handled.
      if (e.defaultPrevented) return;
      if (e.key === 'Escape') close();
      if (e.key === 'ArrowLeft') go(index - 1);
      if (e.key === 'ArrowRight') go(index + 1);
    }
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  });

  // A click on the dark area around the photo closes the viewer.
  function onBackdrop(e: MouseEvent) {
    if (e.target === e.currentTarget) close();
  }

  return (
    <div className="viewer" role="dialog" aria-modal="true" aria-label={title} onClick={onBackdrop}>
      <div className="viewer__bar">
        <span className="viewer__count">
          {index + 1} / {items.length}
        </span>
        <button ref={closeBtn} className="icon-btn icon-btn--round" aria-label="Close" onClick={close}>
          <Close />
        </button>
      </div>
      <div className="viewer__stage" onClick={onBackdrop}>
        {aspect ? (
          <Compare
            before={item.before_url}
            after={item.after_url}
            beforeAlt="The photo as uploaded"
            afterAlt="The sharpened photo"
            aspect={aspect}
          />
        ) : (
          <div className="progress" role="status" aria-label="Loading" />
        )}
      </div>
      <div className="viewer__foot">
        <div className="card__text">
          <p className="viewer__title">{title}</p>
          <p className="card__meta">{meta}</p>
        </div>
        <div className="viewer__actions">
          <button
            className="icon-btn icon-btn--round"
            aria-label="Previous photo"
            onClick={() => go(index - 1)}
            disabled={index === 0}
          >
            <ChevronLeft />
          </button>
          <button
            className="icon-btn icon-btn--round"
            aria-label="Next photo"
            onClick={() => go(index + 1)}
            disabled={index === items.length - 1}
          >
            <ChevronRight />
          </button>
          <a
            className="btn btn--secondary btn--pill"
            href={item.after_url}
            download={`deblurred-${item.id.slice(0, 8)}.jpg`}
          >
            <Download />
            Download
          </a>
        </div>
      </div>
    </div>
  );
}

/** Width / height of an image, once it has loaded. The gallery API does not send the size. */
function useAspect(src: string): number | null {
  const [size, setSize] = useState<{ src: string; aspect: number } | null>(null);
  useEffect(() => {
    const img = new Image();
    img.onload = () => setSize({ src, aspect: img.naturalWidth / img.naturalHeight });
    img.src = src;
    return () => {
      img.onload = null;
    };
  }, [src]);
  return size?.src === src ? size.aspect : null;
}
