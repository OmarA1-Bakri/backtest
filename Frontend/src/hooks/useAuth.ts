import { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import {
  login,
  logout,
  refreshToken,
  clearError,
  selectIsAuthenticated,
  selectUser,
  selectAuthError,
  selectAuthLoading,
} from '../store/slices/authSlice';
import { AppDispatch } from '../store/store';

export const useAuth = () => {
  const dispatch = useDispatch<AppDispatch>();
  const navigate = useNavigate();
  const isAuthenticated = useSelector(selectIsAuthenticated);
  const user = useSelector(selectUser);
  const error = useSelector(selectAuthError);
  const loading = useSelector(selectAuthLoading);

  useEffect(() => {
    const checkTokenExpiration = async () => {
      if (isAuthenticated) {
        const token = sessionStorage.getItem('token');
        const tokenExpiry = sessionStorage.getItem('tokenExpiry');

        if (token && tokenExpiry) {
          const expiryTime = parseInt(tokenExpiry, 10);
          
          // Refresh if token expires in 1 minute or has expired
          if (Date.now() >= expiryTime - 60000) {
            try {
              await dispatch(refreshToken()).unwrap();
            } catch (error) {
              console.error('Token refresh failed:', error);
              handleLogout();
              navigate('/login', { state: { message: 'Session expired. Please login again.' } });
            }
          }
        } else {
          // If no token or expiry time, force logout
          handleLogout();
          navigate('/login');
        }
      }
    };

    const interval = setInterval(checkTokenExpiration, 30000); // Check every 30 seconds
    return () => clearInterval(interval);
  }, [dispatch, isAuthenticated, navigate]);

  const handleLogin = async (email: string, password: string) => {
    try {
      await dispatch(login({ email, password })).unwrap();
      navigate('/dashboard');
    } catch (error: any) {
      console.error('Login failed:', error);
      if (error.status === 401) {
        return 'Invalid email or password';
      }
      return error.message || 'An error occurred during login';
    }
  };

  const handleLogout = () => {
    dispatch(logout());
    navigate('/login');
  };

  const handleError = () => {
    dispatch(clearError());
  };

  return {
    isAuthenticated,
    user,
    error,
    loading,
    login: handleLogin,
    logout: handleLogout,
    clearError: handleError,
  };
};
