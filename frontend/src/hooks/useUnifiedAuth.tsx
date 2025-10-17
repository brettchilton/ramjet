import { useAuth as useSimpleAuth } from '../contexts/SimpleAuthContext';
import { useAuth as useKratosAuth } from '../contexts/AuthContext';

// Unified auth hook that works with both systems
export function useUnifiedAuth() {
  const isSimpleAuth = import.meta.env.VITE_USE_SIMPLE_AUTH === 'true' || import.meta.env.DEV;
  
  if (isSimpleAuth) {
    const auth = useSimpleAuth();
    return {
      user: auth.user,
      loading: auth.loading,
      isAuthenticated: auth.isAuthenticated,
      logout: auth.logout,
    };
  } else {
    const auth = useKratosAuth();
    return {
      user: auth.user,
      loading: auth.loading,
      isAuthenticated: auth.isAuthenticated,
      logout: auth.logout,
    };
  }
}