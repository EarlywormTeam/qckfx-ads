import { useState, useEffect } from 'react';
import axios from 'axios';

export const useAuth = () => {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const checkAuthStatus = async () => {
    try {
      const response = await axios.get('/api/auth/status', { withCredentials: true });
      setIsAuthenticated(response.data.status === 'authenticated');
    } catch (error) {
      console.error('Error checking auth status:', error);
      setIsAuthenticated(false);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    checkAuthStatus();
    // Set up periodic checks (e.g., every 5 minutes)
    const intervalId = setInterval(checkAuthStatus, 5 * 60 * 1000);
    return () => clearInterval(intervalId);
  }, []);

  const signIn = () => {
    // Redirect to WorkOS hosted sign-in page
    window.location.href = '/api/auth/sign_in';
  };

  const signOut = async () => {
    try {
      await axios.post('/api/auth/sign_out', {}, { withCredentials: true });
      setIsAuthenticated(false);
      window.location.href = '/';
    } catch (error) {
      console.error('Error signing out:', error);
    }
  };

  return { isAuthenticated, isLoading, signIn, signOut, checkAuthStatus };
};