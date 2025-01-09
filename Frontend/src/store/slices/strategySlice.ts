import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import axios from 'axios';
import { RootState } from '../store';

interface StrategyParams {
  [key: string]: any;
}

interface Strategy {
  id: string;
  name: string;
  description: string;
  params: StrategyParams;
}

interface StrategyState {
  strategies: Strategy[];
  selectedStrategy: Strategy | null;
  loading: boolean;
  error: string | null;
}

const initialState: StrategyState = {
  strategies: [],
  selectedStrategy: null,
  loading: false,
  error: null,
};

export const fetchStrategies = createAsyncThunk(
  'strategy/fetchStrategies',
  async (_, { getState, rejectWithValue }) => {
    try {
      const state = getState() as RootState;
      const token = state.auth.token;
      
      const response = await axios.get('/api/strategies', {
        headers: { Authorization: `Bearer ${token}` },
      });
      
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.error || 'Failed to fetch strategies');
    }
  }
);

export const saveStrategy = createAsyncThunk(
  'strategy/saveStrategy',
  async (strategy: Partial<Strategy>, { getState, rejectWithValue }) => {
    try {
      const state = getState() as RootState;
      const token = state.auth.token;
      
      const response = await axios.post('/api/strategies', strategy, {
        headers: { Authorization: `Bearer ${token}` },
      });
      
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.error || 'Failed to save strategy');
    }
  }
);

const strategySlice = createSlice({
  name: 'strategy',
  initialState,
  reducers: {
    selectStrategy: (state, action) => {
      state.selectedStrategy = action.payload;
    },
    clearStrategyError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchStrategies.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchStrategies.fulfilled, (state, action) => {
        state.loading = false;
        state.strategies = action.payload;
      })
      .addCase(fetchStrategies.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })
      .addCase(saveStrategy.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(saveStrategy.fulfilled, (state, action) => {
        state.loading = false;
        state.strategies.push(action.payload);
      })
      .addCase(saveStrategy.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      });
  },
});

export const { selectStrategy, clearStrategyError } = strategySlice.actions;
export default strategySlice.reducer;

// Selectors
export const selectStrategies = (state: RootState) => state.strategy.strategies;
export const selectCurrentStrategy = (state: RootState) => state.strategy.selectedStrategy;
export const selectStrategyLoading = (state: RootState) => state.strategy.loading;
export const selectStrategyError = (state: RootState) => state.strategy.error;
