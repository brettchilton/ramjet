import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { kratosService } from '../services/kratosService';

interface User {
  email: string;
  first_name: string;
  last_name: string;
  mobile?: string;
  role?: string;
}

interface Session {
  id: string;
  active: boolean;
  expires_at: string;
  authenticated_at: string;
  identity: {
    id: string;
    schema_id: string;
    schema_url: string;
    traits: User;
  };
}

interface AuthContextType {
  session: Session | null;
  user: User | null;
  loading: boolean;
  isAuthenticated: boolean;
  checkSession: (forceRefresh?: boolean) => Promise<boolean>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);
  const [hasInitialized, setHasInitialized] = useState(false);

  const checkSession = useCallback(async (forceRefresh = false) => {
    console.log('[AuthProvider] Checking session, forceRefresh:', forceRefresh);
    try {
      const data = await kratosService.checkSession(forceRefresh);
      setSession(data.session);
      return !!data.session?.active;
    } catch (error) {
      console.error('[AuthProvider] Session check failed:', error);
      setSession(null);
      return false;
    } finally {
      setLoading(false);
    }
  }, []);

  const logout = useCallback(async () => {
    await kratosService.logout();
    setSession(null);
  }, []);

  // Initial session check
  useEffect(() => {
    if (!hasInitialized) {
      console.log('[AuthProvider] Initial session check');
      setHasInitialized(true);
      checkSession();
    }
  }, [hasInitialized, checkSession]);

  const value = {
    session,
    user: session?.identity?.traits || null,
    loading,
    isAuthenticated: !!session?.active,
    checkSession,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}