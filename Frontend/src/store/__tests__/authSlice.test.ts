import { configureStore } from '@reduxjs/toolkit';
import authReducer, {
  login,
  logout,
  refreshToken,
  clearError,
} from '../slices/authSlice';

describe('Auth Slice', () => {
  let store: ReturnType<typeof configureStore>;

  beforeEach(() => {
    store = configureStore({
      reducer: { auth: authReducer },
    });
  });

  it('should handle initial state', () => {
    const state = store.getState().auth;
    expect(state.user).toBeNull();
    expect(state.isAuthenticated).toBeFalsy();
    expect(state.loading).toBeFalsy();
    expect(state.error).toBeNull();
  });

  it('should handle login.pending', () => {
    store.dispatch(login.pending('', { email: 'test@test.com', password: 'password' }));
    const state = store.getState().auth;
    expect(state.loading).toBeTruthy();
    expect(state.error).toBeNull();
  });

  it('should handle login.fulfilled', () => {
    const mockUser = { id: 1, email: 'test@test.com', username: 'test' };
    const mockPayload = {
      user: mockUser,
      token: 'mock-token',
      refreshToken: 'mock-refresh-token',
    };

    store.dispatch(login.fulfilled(mockPayload, '', { email: 'test@test.com', password: 'password' }));
    const state = store.getState().auth;
    
    expect(state.loading).toBeFalsy();
    expect(state.isAuthenticated).toBeTruthy();
    expect(state.user).toEqual(mockUser);
    expect(state.token).toBe('mock-token');
    expect(state.refreshToken).toBe('mock-refresh-token');
  });

  it('should handle login.rejected', () => {
    store.dispatch(login.rejected(null, '', { email: 'test@test.com', password: 'password' }, 'Login failed'));
    const state = store.getState().auth;
    
    expect(state.loading).toBeFalsy();
    expect(state.error).toBe('Login failed');
    expect(state.isAuthenticated).toBeFalsy();
  });

  it('should handle logout', () => {
    // First login
    const mockUser = { id: 1, email: 'test@test.com', username: 'test' };
    store.dispatch(login.fulfilled({
      user: mockUser,
      token: 'mock-token',
      refreshToken: 'mock-refresh-token',
    }, '', { email: 'test@test.com', password: 'password' }));

    // Then logout
    store.dispatch(logout());
    const state = store.getState().auth;
    
    expect(state.user).toBeNull();
    expect(state.token).toBeNull();
    expect(state.refreshToken).toBeNull();
    expect(state.isAuthenticated).toBeFalsy();
  });

  it('should handle refreshToken.fulfilled', () => {
    store.dispatch(refreshToken.fulfilled({ token: 'new-token' }, ''));
    const state = store.getState().auth;
    
    expect(state.token).toBe('new-token');
  });

  it('should handle clearError', () => {
    // First set an error
    store.dispatch(login.rejected(null, '', { email: 'test@test.com', password: 'password' }, 'Login failed'));
    
    // Then clear it
    store.dispatch(clearError());
    const state = store.getState().auth;
    
    expect(state.error).toBeNull();
  });
});
