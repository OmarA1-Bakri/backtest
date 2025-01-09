import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import axios from 'axios';
import { RootState } from '../store';

interface BacktestResult {
  id: string;
  strategyId: string;
  startDate: string;
  endDate: string;
  initialCapital: number;
  finalCapital: number;
  returns: number;
  sharpeRatio: number;
  maxDrawdown: number;
  trades: any[];
  metrics: {
    [key: string]: number;
  };
}

interface BacktestState {
  results: BacktestResult[];
  currentResult: BacktestResult | null;
  loading: boolean;
  error: string | null;
}

const initialState: BacktestState = {
  results: [],
  currentResult: null,
  loading: false,
  error: null,
};

export const runBacktest = createAsyncThunk(
  'backtest/runBacktest',
  async (params: {
    strategyId: string;
    startDate: string;
    endDate: string;
    initialCapital: number;
  }, { getState, rejectWithValue }) => {
    try {
      const state = getState() as RootState;
      const token = state.auth.token;
      
      const response = await axios.post('/api/backtest', params, {
        headers: { Authorization: `Bearer ${token}` },
      });
      
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.error || 'Backtest failed');
    }
  }
);

export const fetchBacktestResults = createAsyncThunk(
  'backtest/fetchResults',
  async (_, { getState, rejectWithValue }) => {
    try {
      const state = getState() as RootState;
      const token = state.auth.token;
      
      const response = await axios.get('/api/backtest/results', {
        headers: { Authorization: `Bearer ${token}` },
      });
      
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.error || 'Failed to fetch backtest results');
    }
  }
);

const backtestSlice = createSlice({
  name: 'backtest',
  initialState,
  reducers: {
    selectBacktestResult: (state, action) => {
      state.currentResult = action.payload;
    },
    clearBacktestError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(runBacktest.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(runBacktest.fulfilled, (state, action) => {
        state.loading = false;
        state.currentResult = action.payload;
        state.results.unshift(action.payload);
      })
      .addCase(runBacktest.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })
      .addCase(fetchBacktestResults.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchBacktestResults.fulfilled, (state, action) => {
        state.loading = false;
        state.results = action.payload;
      })
      .addCase(fetchBacktestResults.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      });
  },
});

export const { selectBacktestResult, clearBacktestError } = backtestSlice.actions;
export default backtestSlice.reducer;

// Selectors
export const selectBacktestResults = (state: RootState) => state.backtest.results;
export const selectCurrentBacktest = (state: RootState) => state.backtest.currentResult;
export const selectBacktestLoading = (state: RootState) => state.backtest.loading;
export const selectBacktestError = (state: RootState) => state.backtest.error;
