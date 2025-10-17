interface ApiRequestOptions extends RequestInit {
  skipAuth?: boolean;
}

class ApiClient {
  private baseUrl: string;

  constructor() {
    // Use relative URL in production, absolute in development
    this.baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8006';
  }

  private getAuthToken(): string | null {
    return localStorage.getItem('authToken');
  }

  private async makeRequest(url: string, options: ApiRequestOptions = {}): Promise<Response> {
    const { skipAuth = false, headers = {}, ...restOptions } = options;
    const token = this.getAuthToken();

    // Build headers
    const requestHeaders: Record<string, string> = {
      ...(headers as Record<string, string>)
    };

    // Add authentication header if token exists and not skipped
    if (!skipAuth && token) {
      requestHeaders['Authorization'] = `Bearer ${token}`;
    }

    // Make the request
    const response = await fetch(url, {
      ...restOptions,
      headers: requestHeaders,
      credentials: 'include' // Always include cookies
    });

    // Handle 401 errors
    if (response.status === 401 && !skipAuth) {
      // Clear auth token and redirect to login
      localStorage.removeItem('authToken');
      window.location.href = '/auth/login';
    }

    return response;
  }

  async get(endpoint: string, options?: ApiRequestOptions): Promise<Response> {
    const url = `${this.baseUrl}${endpoint}`;
    return this.makeRequest(url, {
      ...options,
      method: 'GET'
    });
  }

  async post(endpoint: string, body?: any, options?: ApiRequestOptions): Promise<Response> {
    const url = `${this.baseUrl}${endpoint}`;
    const isFormData = body instanceof FormData;
    
    return this.makeRequest(url, {
      ...options,
      method: 'POST',
      body: isFormData ? body : JSON.stringify(body),
      headers: isFormData ? options?.headers : {
        'Content-Type': 'application/json',
        ...options?.headers
      }
    });
  }

  async put(endpoint: string, body?: any, options?: ApiRequestOptions): Promise<Response> {
    const url = `${this.baseUrl}${endpoint}`;
    return this.makeRequest(url, {
      ...options,
      method: 'PUT',
      body: JSON.stringify(body),
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers
      }
    });
  }

  async delete(endpoint: string, options?: ApiRequestOptions): Promise<Response> {
    const url = `${this.baseUrl}${endpoint}`;
    return this.makeRequest(url, {
      ...options,
      method: 'DELETE'
    });
  }

  async upload(endpoint: string, formData: FormData, options?: ApiRequestOptions): Promise<Response> {
    return this.post(endpoint, formData, options);
  }
}

// Export a singleton instance
export const apiClient = new ApiClient();

// Export the class for testing or custom instances
export default ApiClient;