import { useEffect, useRef, useState } from 'react';
import { Link as RouterLink } from '@tanstack/react-router';
import { createFileRoute, useNavigate } from '@tanstack/react-router';
import { useKratos } from '../../hooks/useKratos';
import { KratosFlow } from '../../components/KratosFlow';
import { ColorModeContext } from '../../ColorModeContext';
import { Sun } from 'lucide-react';
import { useContext } from 'react';

export const Route = createFileRoute('/auth/login')({ component: LoginPage });

function LoginPage() {
  const navigate = useNavigate();
  const colorMode = useContext(ColorModeContext);
  const { initFlow, submitFlow, isAuthenticated, loading: authLoading } = useKratos();
  const [flow, setFlow] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const initializingRef = useRef(false);

  useEffect(() => {
    console.log('[LoginPage] Effect triggered - authLoading:', authLoading, 'isAuthenticated:', isAuthenticated, 'flow:', !!flow);
    
    // Wait for auth session check to complete
    if (authLoading) {
      console.log('[LoginPage] Waiting for auth check to complete...');
      return;
    }

    // If authenticated, redirect to dashboard
    if (isAuthenticated) {
      console.log('[LoginPage] User is authenticated, redirecting to dashboard...');
      navigate({ to: '/dashboard' });
      return;
    }

    // Prevent concurrent initialization
    if (initializingRef.current || flow) {
      console.log('[LoginPage] Flow initialization already in progress or completed');
      return;
    }

    const setupFlow = async () => {
      initializingRef.current = true;
      setError(null);
      
      try {
        console.log('[LoginPage] Starting flow initialization...');
        const loginFlow = await initFlow('login');
        console.log('[LoginPage] Flow initialized successfully:', loginFlow);
        setFlow(loginFlow);
      } catch (error: any) {
        console.error('[LoginPage] Flow initialization failed:', error);
        console.error('[LoginPage] Error details:', error.message, error.stack);
        
        // If already authenticated, redirect to dashboard
        if (error.message === 'Already authenticated') {
          console.log('[LoginPage] User already authenticated, redirecting...');
          navigate({ to: '/dashboard' });
          return;
        }
        
        setError('Failed to initialize login. Please refresh the page.');
      } finally {
        setLoading(false);
        initializingRef.current = false;
      }
    };

    setupFlow();
  }, [authLoading, isAuthenticated, navigate, flow, initFlow]);

  const handleSubmit = async (data: any) => {
    const result = await submitFlow('login', flow.id, data);
    
    if (result.success) {
      // Wait a moment for the session to be established
      setTimeout(() => {
        // Force a page reload to ensure auth state is refreshed
        window.location.href = '/dashboard';
      }, 100);
    }
    
    return result;
  };

  if (loading || authLoading) {
    return (
      <div className="flex justify-center mt-20">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-muted-foreground border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="max-w-sm mx-auto mt-16">
      <div className="border rounded-lg p-6">
        <div className="flex justify-between mb-3">
          <h1 className="text-xl font-semibold">Sign In</h1>
          <button
            className="h-8 w-8 inline-flex items-center justify-center rounded-md hover:bg-muted text-muted-foreground"
            onClick={colorMode.toggleColorMode}
            aria-label="Toggle theme"
          >
            <Sun size={18} />
          </button>
        </div>

        {error && (
          <div className="mb-2 p-2 rounded bg-red-50 text-red-700 text-sm">
            {error}
          </div>
        )}

        {flow && (
          <KratosFlow flow={flow} onSubmit={handleSubmit} />
        )}

        {!flow && !error && (
          <div className="text-center py-6">
            <div className="mx-auto h-6 w-6 animate-spin rounded-full border-2 border-muted-foreground border-t-transparent" />
            <div className="text-sm text-muted-foreground mt-2">Initializing login...</div>
          </div>
        )}

        <div className="mt-3 text-center text-sm">
          <div>
            Don't have an account?{' '}
            <RouterLink to="/auth/registration" className="underline">Sign up</RouterLink>
          </div>
          <div className="mt-1">
            <RouterLink to="/auth/recovery" className="underline">Forgot password?</RouterLink>
          </div>
        </div>
      </div>
    </div>
  );
}