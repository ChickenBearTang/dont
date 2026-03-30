import { createRoot } from 'react-dom/client';
import { App } from '@/app/App';

const rootElement = document.getElementById('root');
if (!rootElement) throw new Error('루트 요소를 찾지 못했습니다.');

createRoot(rootElement).render(<App />);
