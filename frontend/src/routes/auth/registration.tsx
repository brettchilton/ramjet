import { useEffect, useRef, useState, useContext } from 'react';
import { Link as RouterLink } from '@tanstack/react-router';
import { createFileRoute, useNavigate } from '@tanstack/react-router';
import { useKratos } from '../../hooks/useKratos';
import { KratosFlow } from '../../components/KratosFlow';
import { ColorModeContext } from '../../ColorModeContext';
import { Sun } from 'lucide-react';

export const Route = createFileRoute('/auth/registration')({ component: RegistrationPage });

function RegistrationPage() {
  const navigate = useNavigate();
  const colorMode = useContext(ColorModeContext);
  const { initFlow, submitFlow, isAuthenticated, loading: authLoading } = useKratos();
  const [flow, setFlow] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const initializingRef = useRef(false);

  useEffect(() => {
    // Wait for auth session check to complete
    if (authLoading) return;

    // Redirect if already authenticated
    if (isAuthenticated) {
      navigate({ to: '/dashboard' });
      return;
    }

    // Prevent concurrent initialization
    if (initializingRef.current || flow) return;

    // Initialize registration flow
    const setupFlow = async () => {
      initializingRef.current = true;
      setError(null);
      
      try {
        const registrationFlow = await initFlow('registration');
        setFlow(registrationFlow);
      } catch (error: any) {
        console.error('Failed to initialize registration flow:', error);
        setError('Failed to initialize registration. Please refresh the page.');
      } finally {
        setLoading(false);
        initializingRef.current = false;
      }
    };

    setupFlow();
  }, [authLoading, isAuthenticated, navigate, flow, initFlow]);

  const handleSubmit = async (data: any) => {
    const result = await submitFlow('registration', flow.id, data);
    
    if (result.success) {
      // Redirect to dashboard or verification page on successful registration
      if (result.data.session) {
        navigate({ to: '/dashboard' });
      } else {
        navigate({ to: '/auth/verification' });
      }
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
          <h1 className="text-xl font-semibold">Create Account</h1>
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
            <div className="text-sm text-muted-foreground mt-2">Initializing registration...</div>
          </div>
        )}

        <div className="mt-3 text-center text-sm">
          <div>
            Already have an account?{' '}
            <RouterLink to="/auth/login" className="underline">Sign in</RouterLink>
          </div>
        </div>
      </div>
    </div>
  );
}