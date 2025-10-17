// Universal auth hook that works with both Kratos and Simple auth
const useSimpleAuth = import.meta.env.VITE_USE_SIMPLE_AUTH === 'true' || import.meta.env.DEV;

export const useAuth = useSimpleAuth 
  ? require('../contexts/SimpleAuthContext').useAuth
  : require('../contexts/AuthContext').useAuth;

// For backward compatibility with existing code using useKratos
export { useKratos } from '../hooks/useKratos';