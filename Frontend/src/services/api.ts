import axios from 'axios';

const API_BASE_URL = 'http://localhost:5000/api';

interface BacktestParams {
  strategy?: string;
  params?: { [key: string]: unknown };
  startDate?: string;
  endDate?: string;
  symbol?: string;
}

interface Strategy {
  name: string;
  parameters: { [key: string]: unknown };
}

export const api = {
  runBacktest: async (params: BacktestParams) => {
    try {
      console.log('API Request: runBacktest', params);
      const response = await axios.post(`${API_BASE_URL}/run_backtest`, params);
      console.log('API Response: runBacktest', response);
      return response.data;
    } catch (error) {
      console.error('API Error: runBacktest', error);
      throw error;
    }
  },

  getPerformanceMetrics: async (returns: number[], trades: number[]) => {
    try {
      console.log('API Request: getPerformanceMetrics', { returns, trades });
      const response = await axios.post(`${API_BASE_URL}/get_performance_metrics`, { returns, trades });
      console.log('API Response: getPerformanceMetrics', response);
      return response.data;
    } catch (error) {
      console.error('API Error: getPerformanceMetrics', error);
      throw error;
    }
  },
  
  getStrategies: async () : Promise<Strategy[]> => {
    try {
      console.log('API Request: getStrategies');
      const response = await axios.get(`${API_BASE_URL}/strategies`);
      console.log('API Response: getStrategies', response);
      return response.data;
    } catch (error) {
      console.error('API Error: getStrategies', error);
      throw error;
    }
  }
};
