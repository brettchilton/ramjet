import { Outlet } from '@tanstack/react-router';
import { Header } from './Header';

export function AppLayout() {
  return (
    <div className="min-h-screen bg-white dark:bg-gray-950">
      <Header />
      <main className="pt-14">
        <div className="max-w-7xl mx-auto p-6">
          <Outlet />
        </div>
      </main>
    </div>
  );
}