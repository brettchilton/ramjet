import React, { useState, useMemo, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { RouterProvider, createRouter } from '@tanstack/react-router';
import { routeTree } from './routeTree.gen';
import './index.css';
import { AuthProvider } from './contexts/AuthContext';
import { SimpleAuthProvider } from './contexts/SimpleAuthContext';
import { ColorModeContext } from './ColorModeContext';

// Create a client for TanStack Query
const queryClient = new QueryClient();

// Create a TanStack Router instance
const router = createRouter({ 
  routeTree,
  defaultNotFoundComponent: () => {
    console.log('Not found component rendering');
    return (
      <div style={{ padding: '2rem', textAlign: 'center' }}>
        <h1>404 - Page Not Found</h1>
        <p>The page you're looking for doesn't exist.</p>
        <p>Current path: {window.location.pathname}</p>
        <a href="/">Go to Home</a>
      </div>
    );
  },
});

console.log('Router created:', router);
console.log('Route tree:', routeTree);

declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router;
  }
}

function App() {
  // Initialize theme state
  const [mode, setMode] = useState<'light' | 'dark'>('light');
  const [isInitialized, setIsInitialized] = useState(false);
  
  // Initialize theme on mount
  useEffect(() => {
    const initializeTheme = () => {
      // Check localStorage first
      const stored = localStorage.getItem('theme');
      let initialMode: 'light' | 'dark';
      
      if (stored === 'light' || stored === 'dark') {
        initialMode = stored;
      } else {
        // Check system preference
        initialMode = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
        localStorage.setItem('theme', initialMode);
      }
      
      console.log('Initializing theme to:', initialMode);
      setMode(initialMode);
      
      // Apply to HTML immediately
      const root = document.documentElement;
      if (initialMode === 'dark') {
        root.classList.add('dark');
      } else {
        root.classList.remove('dark');
      }
      
      setIsInitialized(true);
    };
    
    initializeTheme();
  }, []);
  
  const colorMode = useMemo(
    () => ({ 
      mode,
      toggleColorMode: () => {
        setMode((prev) => {
          const newMode = prev === 'light' ? 'dark' : 'light';
          console.log('Toggling theme from', prev, 'to', newMode);
          localStorage.setItem('theme', newMode);
          
          // Apply to HTML immediately
          const root = document.documentElement;
          if (newMode === 'dark') {
            root.classList.add('dark');
          } else {
            root.classList.remove('dark');
          }
          
          return newMode;
        });
      }
    }),
    [mode]
  );
  
  // Don't render until theme is initialized to prevent flash
  if (!isInitialized) {
    return <div>Loading...</div>;
  }

  // Use simple auth in development, Kratos in production
  const useSimpleAuth = import.meta.env.VITE_USE_SIMPLE_AUTH === 'true' || import.meta.env.DEV;
  const AuthProviderComponent = useSimpleAuth ? SimpleAuthProvider : AuthProvider;

  return (
    <ColorModeContext.Provider value={colorMode}>
      <QueryClientProvider client={queryClient}>
        <AuthProviderComponent>
          <RouterProvider router={router} />
        </AuthProviderComponent>
      </QueryClientProvider>
    </ColorModeContext.Provider>
  );
}

// Add error handling
window.addEventListener('error', (e) => {
  console.error('Global error:', e.error);
  const errorDiv = document.createElement('div');
  errorDiv.innerHTML = `<h1>Error: ${e.error?.message || 'Unknown error'}</h1><pre>${e.error?.stack || ''}</pre>`;
  errorDiv.style.color = 'red';
  errorDiv.style.padding = '20px';
  document.body.appendChild(errorDiv);
});

const rootElement = document.getElementById('root');
console.log('Root element:', rootElement);
console.log('Router:', router);

if (!rootElement) {
  document.body.innerHTML = '<h1>Error: Root element not found</h1>';
} else {
  try {
    ReactDOM.createRoot(rootElement).render(
      <App />
    );
    console.log('App rendered successfully');
  } catch (error) {
    console.error('Render error:', error);
    document.body.innerHTML = `<h1>Render Error</h1><pre>${error}</pre>`;
  }
}
