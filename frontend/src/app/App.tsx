import { StrictMode } from 'react';
import { RouterProvider } from 'react-router-dom';
import { router } from '@/app/router';
import { ToastContainer } from '@/shared/components/ToastContainer';
import '@/styles/index.css';

export function App() {
  return (
    <StrictMode>
      <ToastContainer />
      <RouterProvider router={router} />
    </StrictMode>
  );
}
