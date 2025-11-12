import { Component, type ErrorInfo, type ReactNode } from 'react';

type ErrorBoundaryState = {
  error: Error | null;
  info: string | null;
};

type ErrorBoundaryProps = {
  children: ReactNode;
};

class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  state: ErrorBoundaryState = {
    error: null,
    info: null,
  };

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { error, info: null };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    // eslint-disable-next-line no-console
    console.error('Frontend render error', error, info);
    this.setState({ info: info.componentStack ?? null });
  }

  resetError = () => {
    this.setState({ error: null, info: null });
  };

  render() {
    const { error, info } = this.state;
    const { children } = this.props;

    if (error) {
      return (
        <div className="flex h-screen flex-col items-center justify-center gap-4 bg-gray-900 p-6 text-center text-white">
          <div className="max-w-xl rounded-lg border border-white/20 bg-black/40 p-6 shadow-lg shadow-rose-500/20">
            <h1 className="text-2xl font-semibold">Что-то пошло не так 😔</h1>
            <p className="mt-2 font-mono text-sm text-rose-200">
              {error.message}
            </p>
            {info ? (
              <pre className="mt-4 max-h-48 overflow-y-auto whitespace-pre-wrap rounded bg-black/60 p-4 text-left text-xs text-amber-100">
                {info}
              </pre>
            ) : null}
            <button
              type="button"
              onClick={this.resetError}
              className="mt-4 inline-flex items-center gap-2 rounded-lg bg-rose-500 px-4 py-2 text-sm font-medium text-white transition hover:bg-rose-400"
            >
              Попробовать снова
            </button>
          </div>
        </div>
      );
    }

    return children;
  }
}

export default ErrorBoundary;
