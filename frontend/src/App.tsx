import { RouterProvider } from 'react-router-dom';
import { router } from '@/app/router';
import { ToastContainer } from '@/shared/components/ToastContainer';
import '@/styles/index.css';

function App() {
  return (
    <>
      <RouterProvider router={router} />
      <ToastContainer />
    </>
  );
}

export default App;
