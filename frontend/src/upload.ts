// The backend's defaults (DEBLUR_MAX_UPLOAD_MB and DEBLUR_FULL_SIDE).
const MAX_BYTES = 15 * 1024 * 1024;
const MAX_SIDE = 1600;

/** The file to send. A photo over the upload limit is shrunk in the browser to the size the
 * backend would shrink it to anyway, if the browser can decode it (HEIC only in Safari).
 * PNG, not JPEG: deblurring amplifies JPEG artifacts. */
export async function prepareUpload(file: File): Promise<{ blob: Blob; name: string }> {
  if (file.size <= MAX_BYTES) return { blob: file, name: file.name };

  let bitmap: ImageBitmap;
  try {
    // from-image applies the EXIF rotation, which the canvas would otherwise lose.
    bitmap = await createImageBitmap(file, { imageOrientation: 'from-image' });
  } catch {
    throw new Error('This photo is larger than 15 MB. Try a smaller one.');
  }
  const scale = Math.min(1, MAX_SIDE / Math.max(bitmap.width, bitmap.height));
  const canvas = document.createElement('canvas');
  canvas.width = Math.round(bitmap.width * scale);
  canvas.height = Math.round(bitmap.height * scale);
  const ctx = canvas.getContext('2d');
  if (!ctx) throw new Error('This photo is larger than 15 MB. Try a smaller one.');
  ctx.imageSmoothingQuality = 'high';
  ctx.drawImage(bitmap, 0, 0, canvas.width, canvas.height);
  bitmap.close();

  const blob = await new Promise<Blob | null>((resolve) => canvas.toBlob(resolve, 'image/png'));
  if (!blob) throw new Error('This photo is larger than 15 MB. Try a smaller one.');
  return { blob, name: 'photo.png' };
}
