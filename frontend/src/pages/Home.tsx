import { useRef, useState, type ChangeEvent, type DragEvent } from 'react';

import { messageOf, uploadPhoto } from '../api';
import { Compare } from '../components/Compare';
import { Camera, Picture } from '../components/icons';
import { Brand, GalleryLink, TopBar } from '../components/TopBar';
import { useMediaQuery } from '../hooks';
import { navigate, paths } from '../router';
import { prepareUpload } from '../upload';

export function Home() {
  // Phones get a camera button; on a computer it would only open the file dialog again.
  const touch = useMediaQuery('(pointer: coarse)');
  const cameraInput = useRef<HTMLInputElement>(null);
  const libraryInput = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function upload(file: File) {
    setUploading(true);
    setError(null);
    try {
      const { blob, name } = await prepareUpload(file);
      const photo = await uploadPhoto(blob, name);
      navigate(paths.photo(photo.id));
    } catch (err) {
      setError(messageOf(err));
      setUploading(false);
    }
  }

  function onPick(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    // Cleared so that picking the same file again still fires onChange.
    e.target.value = '';
    if (file) void upload(file);
  }

  function onDrop(e: DragEvent) {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file && !uploading) void upload(file);
  }

  return (
    <div className="screen screen--home" onDragOver={(e) => e.preventDefault()} onDrop={onDrop}>
      <TopBar left={<Brand />} right={<GalleryLink />} />
      <div className="home">
        <Compare
          before="/example/before.jpg"
          after="/example/after.jpg"
          beforeAlt="A photo of a staircase, blurred by camera motion"
          afterAlt="The same photo after deblurring"
          aspect={1}
        />
        <div className="home__text">
          <h1 className="title title--hero">Fix a blurry photo</h1>
          <p className="lead">Works on shaky and out-of-focus shots. No neural networks, just math.</p>
          <div className="spacer" />
          <div className="btn-stack">
            {uploading && (
              <div className="uploading" role="status">
                Uploading…
                <div className="progress" />
              </div>
            )}
            {error && (
              <p className="error" role="alert">
                {error}
              </p>
            )}
            {touch && (
              <button
                className="btn btn--primary"
                onClick={() => cameraInput.current?.click()}
                disabled={uploading}
              >
                <Camera />
                Take a photo
              </button>
            )}
            <button
              className={`btn ${touch ? 'btn--secondary' : 'btn--primary'}`}
              onClick={() => libraryInput.current?.click()}
              disabled={uploading}
            >
              <Picture />
              {touch ? 'Choose from library' : 'Choose a photo'}
            </button>
          </div>
          <p className="fine">
            JPEG, PNG or HEIC up to 15 MB{touch ? '' : ', or drop it anywhere on this page'}. Photos
            are deleted after 24 hours unless you save them to the gallery.
          </p>
          {/* capture opens the camera directly on phones. */}
          <input ref={cameraInput} type="file" accept="image/*" capture="environment" hidden onChange={onPick} />
          <input ref={libraryInput} type="file" accept="image/*,.heic,.heif" hidden onChange={onPick} />
        </div>
      </div>
    </div>
  );
}
