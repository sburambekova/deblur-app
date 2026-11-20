import { useEffect, useState } from 'react';

import { listGallery, messageOf, removeFromGallery, type GalleryItem } from '../api';
import { Trash } from '../components/icons';
import { BackLink, TopBar } from '../components/TopBar';
import { describeKernel, describeMethod } from '../params';
import { paths } from '../router';

const date = new Intl.DateTimeFormat('en', { day: 'numeric', month: 'short' });

export function Gallery() {
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
    </div>
  );
}

function GalleryCard({ item, onRemove }: { item: GalleryItem; onRemove: () => void }) {
  const kernel = describeKernel(item.params);
  return (
    <article className="card">
      <div className="pair">
        <figure>
          <img src={item.before_url} alt="Before" loading="lazy" decoding="async" />
          <span className="chip chip--bl chip--sm">Before</span>
        </figure>
        <figure>
          <img src={item.after_url} alt="After" loading="lazy" decoding="async" />
          <span className="chip chip--bl chip--sm">After</span>
        </figure>
      </div>
      <div className="card__foot">
        <div className="card__text">
          <p className="card__title">{item.caption ?? kernel}</p>
          <p className="card__meta">
            {item.caption ? `${kernel} · ` : ''}
            {describeMethod(item.params)} · {date.format(new Date(item.created_at))}
          </p>
        </div>
        <button className="icon-btn" aria-label="Remove from gallery" onClick={onRemove}>
          <Trash />
        </button>
      </div>
    </article>
  );
}
