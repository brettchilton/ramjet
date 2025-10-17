import { useEffect } from 'react';
import { createFileRoute } from '@tanstack/react-router';
import { useUnifiedAuth } from '../hooks/useUnifiedAuth';

export const Route = createFileRoute('/logout')({ component: LogoutPage });

function LogoutPage() {
  const { logout } = useUnifiedAuth();

  useEffect(() => {
    logout();
  }, [logout]);

  return (
    <div className="flex flex-col items-center mt-20">
      <div className="h-6 w-6 animate-spin rounded-full border-2 border-muted-foreground border-t-transparent" />
      <p className="mt-2 text-muted-foreground">Logging out...</p>
    </div>
  );
}