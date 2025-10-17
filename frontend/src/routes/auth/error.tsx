import { createFileRoute, useNavigate } from '@tanstack/react-router';
import { AlertCircle } from 'lucide-react';

export const Route = createFileRoute('/auth/error')({ 
  component: ErrorPage,
  loader: ({ location }) => {
    const searchParams = new URLSearchParams(location.search);
    return {
      error: searchParams.get('error') || 'An unknown error occurred',
      id: searchParams.get('id'),
    };
  },
});

function ErrorPage() {
  const navigate = useNavigate();
  const { error, id } = Route.useLoaderData();

  return (
    <div className="max-w-md mx-auto mt-16">
      <div className="border rounded-lg p-6 text-center">
        <div className="text-red-500 mb-3 flex justify-center">
          <AlertCircle size={48} />
        </div>
        <h1 className="text-xl font-semibold mb-2">Authentication Error</h1>
        <div className="mb-3 text-left border border-red-200 bg-red-50 text-red-700 rounded p-3">
          {error}
        </div>
        {id && (
          <p className="text-sm text-muted-foreground mb-3">Error ID: {id}</p>
        )}
        <div className="flex gap-2 justify-center">
          <button
            onClick={() => navigate({ to: '/auth/login' })}
            className="inline-flex items-center rounded-md bg-primary px-4 py-2 text-primary-foreground hover:opacity-90 transition"
          >
            Back to Login
          </button>
          <button
            onClick={() => navigate({ to: '/' })}
            className="inline-flex items-center rounded-md border px-4 py-2 hover:bg-muted transition"
          >
            Go Home
          </button>
        </div>
      </div>
    </div>
  );
}