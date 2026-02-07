import { useEffect } from 'react';
import { createFileRoute, useNavigate } from '@tanstack/react-router';
import { useUnifiedAuth } from '../hooks/useUnifiedAuth';

export const Route = createFileRoute('/')({
  component: HomePage,
});

function HomePage() {
  const navigate = useNavigate();
  const { isAuthenticated, loading } = useUnifiedAuth();

  useEffect(() => {
    if (!loading) {
      if (isAuthenticated) {
        navigate({ to: '/orders', replace: true });
      } else {
        navigate({ to: '/login', replace: true });
      }
    }
  }, [isAuthenticated, loading, navigate]);

  return (
    <div className="flex justify-center items-center h-screen">
      <div className="h-6 w-6 animate-spin rounded-full border-2 border-muted-foreground border-t-transparent" />
    </div>
  );
}