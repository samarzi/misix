import { createRoot } from 'react-dom/client';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import './index.css';
import App from './App.tsx';
import ErrorBoundary from './components/ErrorBoundary.tsx';

const queryClient = new QueryClient();

createRoot(document.getElementById('root')!).render(
  <QueryClientProvider client={queryClient}>
    <ErrorBoundary>
      <App />
    </ErrorBoundary>
    <ReactQueryDevtools initialIsOpen={false} />
  </QueryClientProvider>,
);
