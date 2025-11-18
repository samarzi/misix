import { useAuth } from './features/auth/hooks/useAuth';
import DashboardPage from './pages/DashboardPage';
import Toast from './components/Toast';
import Loader from './components/Loader';

const App = () => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader />
      </div>
    );
  }

  return (
    <>
      <DashboardPage />
      <Toast />
    </>
  );
};

export default App;
