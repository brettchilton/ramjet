import { useEffect, useState } from 'react';
import { } from 'react';
import { createFileRoute } from '@tanstack/react-router';
import { useKratos } from '../../hooks/useKratos';
import { KratosFlow } from '../../components/KratosFlow';

export const Route = createFileRoute('/auth/verification')({ component: VerificationPage });

function VerificationPage() {
  const { initFlow, submitFlow } = useKratos();
  const [flow, setFlow] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [verified, setVerified] = useState(false);

  useEffect(() => {
    // Initialize verification flow
    const setupFlow = async () => {
      try {
        const verificationFlow = await initFlow('verification');
        setFlow(verificationFlow);
      } catch (error) {
        console.error('Failed to initialize verification flow:', error);
      } finally {
        setLoading(false);
      }
    };

    setupFlow();
  }, [initFlow]);

  const handleSubmit = async (data: any) => {
    const result = await submitFlow('verification', flow.id, data);
    
    if (result.success) {
      if (result.data.state === 'passed_challenge') {
        setVerified(true);
      } else {
        // Update flow with new state
        setFlow(result.data);
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

  if (verified) {
    return (
      <div className="max-w-sm mx-auto mt-16">
        <div className="border rounded-lg p-6">
          <div className="rounded border border-green-200 bg-green-50 text-green-700 p-3">
            Your email has been verified successfully! You can now use all features of the application.
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-sm mx-auto mt-16">
      <div className="border rounded-lg p-6">
        <h1 className="text-xl font-semibold mb-3">Verify Your Email</h1>
        <p className="text-sm text-muted-foreground mb-3">
          Please check your email for a verification code. Enter it below to verify your account.
        </p>
        {flow && (
          <KratosFlow flow={flow} onSubmit={handleSubmit} />
        )}
      </div>
    </div>
  );
}