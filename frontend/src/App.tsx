import { RouterProvider } from 'react-router-dom';
import { router } from '@/app/router';
import { ToastContainer } from '@/shared/components/ToastContainer';
import StrictSecretaryModal from '@/components/StrictSecretaryModal';
import '@/App.css';

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
