import { Outlet, useLocation } from '@tanstack/react-router';
import { AppLayout } from './Layout/AppLayout';
// import { AuthProvider } from '../AuthProvider';

export function RootLayout() {
  console.log('RootLayout rendering');
  const location = useLocation();
  
  // List of routes that should not use the AppLayout
  const publicRoutes = ['/login', '/register', '/simple-login', '/simple-register', '/forgot-password', '/reset-password'];
  const isPublicRoute = publicRoutes.some(route => location.pathname.startsWith(route));
  
  if (isPublicRoute) {
    return <Outlet />;
  }
  
  // For authenticated routes, wrap with AppLayout
  return <AppLayout />;
  // return (
  //   <AuthProvider>
  //     <Outlet />
  //   </AuthProvider>
  // );
}