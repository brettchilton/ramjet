import { useAuth as useKratosAuth } from '../contexts/AuthContext';
import { useAuth as useSimpleAuth } from '../contexts/SimpleAuthContext';
import { kratosService } from '../services/kratosService';

// Choose auth based on environment
const useAuth = import.meta.env.VITE_USE_SIMPLE_AUTH === 'true' || import.meta.env.DEV
  ? useSimpleAuth
  : useKratosAuth;

// Re-export the auth hook functionality with the same interface
export function useKratos() {
  const auth = useAuth() as any;
  
  // For simple auth, provide a compatible interface
  if (import.meta.env.VITE_USE_SIMPLE_AUTH === 'true' || import.meta.env.DEV) {
    return {
      session: auth.user ? { 
        active: true, 
        identity: { traits: auth.user } 
      } : null,
      loading: auth.loading,
      checkSession: auth.checkAuth,
      initFlow: async () => { throw new Error('Not implemented in simple auth') },
      submitFlow: async () => { throw new Error('Not implemented in simple auth') },
      logout: auth.logout,
      isAuthenticated: auth.isAuthenticated,
      user: auth.user,
    };
  }
  
  // For Kratos auth
  return {
    session: auth.session,
    loading: auth.loading,
    checkSession: auth.checkSession,
    initFlow: kratosService.initializeFlow.bind(kratosService),
    submitFlow: kratosService.submitFlow.bind(kratosService),
    logout: auth.logout,
    isAuthenticated: auth.isAuthenticated,
    user: auth.user,
  };
}