import { Editor } from './pages/Editor';
import { Gallery } from './pages/Gallery';
import { Home } from './pages/Home';
import { useRoute } from './router';

export function App() {
  const route = useRoute();
  if (route.name === 'gallery') return <Gallery itemId={route.itemId} />;
  if (route.name === 'editor') {
    // key: another photo starts a fresh editor; a job of the same photo keeps its settings.
    return <Editor key={route.photoId} photoId={route.photoId} jobId={route.jobId} />;
  }
  return <Home />;
}
