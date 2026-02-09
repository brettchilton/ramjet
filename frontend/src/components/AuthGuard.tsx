import React, { useEffect } from 'react';
import { useNavigate } from '@tanstack/react-router';
import { useUnifiedAuth } from '../hooks/useUnifiedAuth';

interface AuthGuardProps {
  children: React.ReactNode;
  redirectTo?: string;
}

export function AuthGuard({ children, redirectTo = '/login' }: AuthGuardProps) {
  const navigate = useNavigate();
  const { isAuthenticated, loading } = useUnifiedAuth();

  // Trace renders
  useEffect(() => {
    // Only redirect if we're done loading and not authenticated
    if (!loading && !isAuthenticated) {
      navigate({ to: redirectTo as any });
    }
  }, [loading, isAuthenticated, navigate, redirectTo]);

  // Show loading state while checking authentication
  // FIX: Only show loading if we are not authenticated yet.
  // If we are authenticated but revalidating (loading=true), keep showing the UI.
  if (loading && !isAuthenticated) {
    return (
      <div className="h-screen flex flex-col items-center justify-center">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-muted-foreground border-t-transparent" />
        <div className="mt-2 text-sm text-muted-foreground">Checking authentication...</div>
      </div>
    );
  }

  // Don't render children if not authenticated
  if (!isAuthenticated) {
    return null;
  }

  // Render children if authenticated
  return <>{children}</>;
}