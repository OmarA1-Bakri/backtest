import { configureStore } from '@reduxjs/toolkit';
import authReducer from './slices/authSlice';
import strategyReducer from './slices/strategySlice';
import backtestReducer from './slices/backtestSlice';

export const store = configureStore({
  reducer: {
    auth: authReducer,
    strategy: strategyReducer,
    backtest: backtestReducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        // Ignore these action types
        ignoredActions: ['auth/loginSuccess', 'auth/logout'],
      },
    }),
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
