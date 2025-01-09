import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import axios from 'axios';
import { RootState } from '../store';

interface User {
  id: number;
  email: string;
  username: string;
}

interface AuthState {
  user: User | null;
  token: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  loading: boolean;
  error: { message: string; status: number } | null;
}

const initialState: AuthState = {
  user: null,
  token: sessionStorage.getItem('token'),
  refreshToken: sessionStorage.getItem('refreshToken'),
  isAuthenticated: !!sessionStorage.getItem('token'),
  loading: false,
  error: null,
};

export const login = createAsyncThunk(
  'auth/login',
  async (credentials: { email: string; password: string }, { rejectWithValue }) => {
    try {
      // Get CSRF token first
      const csrfResponse = await axios.get('/api/auth/csrf-token');
      const csrfToken = csrfResponse.data.csrfToken;

      // Set CSRF token in headers
      axios.defaults.headers.common['X-CSRF-Token'] = csrfToken;

      const response = await axios.post('/api/auth/login', credentials);
      const { user, token, refreshToken } = response.data;

      // Store tokens securely
      sessionStorage.setItem('token', token);
      sessionStorage.setItem('refreshToken', refreshToken);
      sessionStorage.setItem('tokenExpiry', String(Date.now() + 15 * 60 * 1000)); // 15 minutes

      return { user, token, refreshToken };
    } catch (error: any) {
      const errorMessage = error.response?.data?.message || 'Login failed';
      return rejectWithValue({ message: errorMessage, status: error.response?.status });
    }
  }
);

export const refreshToken = createAsyncThunk(
  'auth/refreshToken',
  async (_, { getState, rejectWithValue, dispatch }) => {
    try {
      const state = getState() as RootState;
      const refresh = state.auth.refreshToken;
      
      if (!refresh) {
        throw new Error('No refresh token available');
      }

      const response = await axios.post('/api/auth/refresh', {
        refresh_token: refresh,
      });
      
      const { access_token, refresh_token } = response.data;

      // Store new tokens securely
      sessionStorage.setItem('token', access_token);
      sessionStorage.setItem('refreshToken', refresh_token);
      sessionStorage.setItem('tokenExpiry', String(Date.now() + 15 * 60 * 1000));

      return { token: access_token, refreshToken: refresh_token };
    } catch (error: any) {
      // If refresh fails, force logout
      dispatch(logout());
      return rejectWithValue('Session expired. Please login again.');
    }
  }
);

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    logout: (state) => {
      state.user = null;
      state.token = null;
      state.refreshToken = null;
      state.isAuthenticated = false;
      state.error = null;
      // Clear stored tokens
      sessionStorage.removeItem('token');
      sessionStorage.removeItem('refreshToken');
      sessionStorage.removeItem('tokenExpiry');
      // Clear CSRF token
      delete axios.defaults.headers.common['X-CSRF-Token'];
    },
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(login.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(login.fulfilled, (state, action) => {
        state.loading = false;
        state.isAuthenticated = true;
        state.user = action.payload.user;
        state.token = action.payload.token;
        state.refreshToken = action.payload.refreshToken;
      })
      .addCase(login.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      .addCase(refreshToken.fulfilled, (state, action) => {
        state.token = action.payload.token;
        state.refreshToken = action.payload.refreshToken;
      })
      .addCase(refreshToken.rejected, (state, action) => {
        state.error = action.payload;
      });
  },
});

export const { logout, clearError } = authSlice.actions;
export default authSlice.reducer;

// Selectors
export const selectIsAuthenticated = (state: RootState) => state.auth.isAuthenticated;
export const selectUser = (state: RootState) => state.auth.user;
export const selectAuthError = (state: RootState) => state.auth.error;
export const selectAuthLoading = (state: RootState) => state.auth.loading;
