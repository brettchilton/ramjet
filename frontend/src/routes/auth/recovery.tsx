import { useEffect, useState } from 'react';
import { Link as RouterLink } from '@tanstack/react-router';
import { createFileRoute, useNavigate } from '@tanstack/react-router';
import { useKratos } from '../../hooks/useKratos';
import { KratosFlow } from '../../components/KratosFlow';

export const Route = createFileRoute('/auth/recovery')({ component: RecoveryPage });

function RecoveryPage() {
  const navigate = useNavigate();
  const { initFlow, submitFlow } = useKratos();
  const [flow, setFlow] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Initialize recovery flow
    const setupFlow = async () => {
      try {
        const recoveryFlow = await initFlow('recovery');
        setFlow(recoveryFlow);
      } catch (error) {
        console.error('Failed to initialize recovery flow:', error);
      } finally {
        setLoading(false);
      }
    };

    setupFlow();
  }, [initFlow]);

  const handleSubmit = async (data: any) => {
    const result = await submitFlow('recovery', flow.id, data);
    
    if (result.success) {
      // Show success message or redirect
      if (result.data.state === 'sent_email') {
        // Email sent successfully
        setFlow(result.data);
      } else if (result.data.state === 'passed_challenge') {
        // Recovery completed, redirect to login
        navigate({ to: '/auth/login' });
      }
    }
    
    return result;
  };

  if (loading) {
    return (
      <div className="flex justify-center mt-20">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-muted-foreground border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="max-w-sm mx-auto mt-16">
      <div className="border rounded-lg p-6">
        <h1 className="text-xl font-semibold mb-3">Reset Password</h1>
        <p className="text-sm text-muted-foreground mb-3">
          Enter your email address and we'll send you a code to reset your password.
        </p>
        {flow && (
          <KratosFlow flow={flow} onSubmit={handleSubmit} />
        )}
        <div className="mt-3 text-center text-sm">
          <span>Remember your password? </span>
          <RouterLink to="/auth/login" className="underline">Sign in</RouterLink>
        </div>
      </div>
    </div>
  );
}