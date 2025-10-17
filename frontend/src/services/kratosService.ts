import { apiClient } from '../utils/apiClient';

interface KratosSession {
  id: string;
  active: boolean;
  expires_at: string;
  authenticated_at: string;
  identity: {
    id: string;
    schema_id: string;
    schema_url: string;
    traits: {
      email: string;
      first_name: string;
      last_name: string;
      mobile?: string;
      role?: string;
    };
  };
}

interface SessionData {
  session: KratosSession | null;
  access_token: string | null;
  user: any | null;
}

class KratosService {
  private static instance: KratosService;
  private sessionPromise: Promise<SessionData> | null = null;
  private sessionData: SessionData | null = null;
  private lastCheckTime: number = 0;
  private readonly SESSION_CHECK_INTERVAL = 5000; // 5 seconds

  private constructor() {}

  static getInstance(): KratosService {
    if (!KratosService.instance) {
      KratosService.instance = new KratosService();
    }
    return KratosService.instance;
  }

  async checkSession(forceRefresh: boolean = false): Promise<SessionData> {
    const now = Date.now();
    
    // If we have a recent session check and not forcing refresh, return cached data
    if (!forceRefresh && this.sessionData && (now - this.lastCheckTime) < this.SESSION_CHECK_INTERVAL) {
      console.log('[KratosService] Returning cached session data');
      return this.sessionData;
    }

    // If there's already a session check in progress, return that promise
    if (this.sessionPromise && !forceRefresh) {
      console.log('[KratosService] Returning existing session check promise');
      return this.sessionPromise;
    }

    console.log('[KratosService] Starting new session check');
    this.sessionPromise = this.performSessionCheck();
    
    try {
      const result = await this.sessionPromise;
      this.sessionData = result;
      this.lastCheckTime = now;
      return result;
    } finally {
      this.sessionPromise = null;
    }
  }

  private async performSessionCheck(): Promise<SessionData> {
    try {
      const response = await apiClient.get('/auth/kratos/session');
      if (response.ok) {
        const data = await response.json();
        console.log('[KratosService] Session check successful:', !!data.session);
        
        // Store JWT token if provided
        if (data.access_token) {
          localStorage.setItem('authToken', data.access_token);
        }
        
        return {
          session: data.session || null,
          access_token: data.access_token || null,
          user: data.user || null
        };
      } else {
        console.log('[KratosService] Session check failed with status:', response.status);
        return { session: null, access_token: null, user: null };
      }
    } catch (error) {
      console.error('[KratosService] Session check error:', error);
      return { session: null, access_token: null, user: null };
    }
  }

  async initializeFlow(flowType: 'login' | 'registration' | 'recovery' | 'verification' | 'settings') {
    try {
      const url = new URL(window.location.href);
      const existingFlowId = url.searchParams.get('flow');

      // If flow id present, fetch its details
      if (existingFlowId) {
        const resp = await apiClient.get(`/auth/kratos/flows/${flowType}?flow=${existingFlowId}`);
        if (!resp.ok) {
          // If flow is expired or invalid, remove it from URL and create new one
          if (resp.status === 410 || resp.status === 400) {
            const newUrl = new URL(window.location.href);
            newUrl.searchParams.delete('flow');
            window.history.replaceState({}, '', newUrl.toString());
            
            // Initialize new flow via API endpoint
            const proxyResp = await apiClient.get(`/auth/kratos/flows/${flowType}/browser`);
            if (proxyResp.ok) {
              return await proxyResp.json();
            }
          }
          throw new Error(`Failed to fetch ${flowType} flow: ${resp.status}`);
        }
        return await resp.json();
      }

      // No flow ID present, initialize new flow via backend proxy
      console.log(`[KratosService] Initializing ${flowType} flow via backend proxy...`);
      const proxyResp = await apiClient.get(`/auth/kratos/flows/${flowType}/browser`);
      console.log(`[KratosService] Backend proxy response status: ${proxyResp.status}`);
      
      if (proxyResp.ok) {
        const flowData = await proxyResp.json();
        console.log('[KratosService] Flow data received:', flowData);
        // Update URL with flow ID without causing reload
        const newUrl = new URL(window.location.href);
        newUrl.searchParams.set('flow', flowData.id);
        window.history.replaceState({}, '', newUrl.toString());
        return flowData;
      } else if (proxyResp.status === 400) {
        // Check if it's because user is already logged in
        const errorData = await proxyResp.json();
        console.log('[KratosService] 400 error data:', errorData);
        if (errorData.detail?.error?.id === 'session_already_available' || 
            errorData.error?.id === 'session_already_available') {
          throw new Error('Already authenticated');
        }
        throw new Error(errorData.detail?.message || errorData.message || `Failed to initialize ${flowType} flow`);
      } else {
        const errorText = await proxyResp.text();
        console.error(`[KratosService] Backend proxy error ${proxyResp.status}:`, errorText);
        throw new Error(`Failed to initialize ${flowType} flow`);
      }
    } catch (error) {
      console.error(`[KratosService] Error initializing ${flowType} flow:`, error);
      throw error;
    }
  }

  async submitFlow(flowType: string, flowId: string, data: any) {
    try {
      const response = await apiClient.post(`/auth/kratos/flows/${flowType}?flow_id=${flowId}`, data);

      if (response.ok) {
        const result = await response.json();
        
        // If we got a session, invalidate our cache
        if (result.session) {
          this.sessionData = null;
          this.lastCheckTime = 0;
          await this.checkSession(true); // Force refresh
        }
        
        return { success: true, data: result };
      } else {
        const error = await response.json();
        return { success: false, error };
      }
    } catch (error: any) {
      console.error(`[KratosService] Error submitting ${flowType} flow:`, error);
      return { success: false, error };
    }
  }

  async logout() {
    try {
      await apiClient.post('/auth/kratos/logout');
      
      // Clear local state
      this.sessionData = null;
      this.lastCheckTime = 0;
      localStorage.removeItem('authToken');
      
      // Redirect to home
      window.location.href = '/';
    } catch (error) {
      console.error('[KratosService] Logout error:', error);
    }
  }

  clearCache() {
    this.sessionData = null;
    this.lastCheckTime = 0;
  }
}

export const kratosService = KratosService.getInstance();