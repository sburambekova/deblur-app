import type { ReactNode } from 'react';

import { paths } from '../router';
import { ChevronLeft } from './icons';

/** Left and right slots with an optional title in the middle. */
export function TopBar({ left, title, right }: { left?: ReactNode; title?: string; right?: ReactNode }) {
  return (
    <header className="bar">
      <div className="bar__side">{left}</div>
      {title ? <h1 className="bar__title">{title}</h1> : <span />}
      <nav className="bar__side bar__side--end">{right}</nav>
    </header>
  );
}

export function Brand() {
  return (
    <a className="brand" href={paths.home}>
      Deblur
    </a>
  );
}

export function BackLink({ href, label = 'Back' }: { href: string; label?: string }) {
  return (
    <a className="link" href={href}>
      <ChevronLeft />
      {label}
    </a>
  );
}

export function GalleryLink() {
  return (
    <a className="link" href={paths.gallery}>
      Gallery
    </a>
  );
}
