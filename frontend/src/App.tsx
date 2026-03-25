import { RouterProvider } from 'react-router-dom';
import { router } from '@/app/router';
import { ToastContainer } from '@/shared/components/ToastContainer';
import StrictSecretaryModal from '@/components/StrictSecretaryModal';
import '@/styles/index.css';

function App() {
  return (
    <>
      <RouterProvider router={router} />
      <ToastContainer />
      <StrictSecretaryModal />
    </>
  );
}

export default App;
