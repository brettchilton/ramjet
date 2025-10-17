import { createFileRoute } from '@tanstack/react-router';

export const Route = createFileRoute('/login')({ component: LoginRedirect });

function LoginRedirect() {
  // Redirect to appropriate login based on auth system
  const useSimpleAuth = import.meta.env.VITE_USE_SIMPLE_AUTH === 'true' || import.meta.env.DEV;
  
  if (useSimpleAuth) {
    window.location.href = '/simple-login';
  } else {
    window.location.href = '/auth/login';
  }
  
  return null;
}