import { createFileRoute } from '@tanstack/react-router';
import { AuthGuard } from '../components/AuthGuard';

export const Route = createFileRoute('/dashboard')({ component: DashboardPage });

function DashboardPage() {
  return (
    <AuthGuard>
      <div className="min-h-screen">
        {/* Empty page - header is in the layout */}
      </div>
    </AuthGuard>
  );
}