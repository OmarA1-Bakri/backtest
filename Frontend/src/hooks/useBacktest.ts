import { useDispatch, useSelector } from 'react-redux';
import {
  runBacktest,
  fetchBacktestResults,
  selectBacktestResults,
  selectCurrentBacktest,
  selectBacktestLoading,
  selectBacktestError,
  selectBacktestResult,
} from '../store/slices/backtestSlice';
import { AppDispatch } from '../store/store';

export const useBacktest = () => {
  const dispatch = useDispatch<AppDispatch>();
  const results = useSelector(selectBacktestResults);
  const currentResult = useSelector(selectCurrentBacktest);
  const loading = useSelector(selectBacktestLoading);
  const error = useSelector(selectBacktestError);

  const executeBacktest = async (params: {
    strategyId: string;
    startDate: string;
    endDate: string;
    initialCapital: number;
  }) => {
    try {
      const result = await dispatch(runBacktest(params)).unwrap();
      return result;
    } catch (error) {
      console.error('Backtest execution failed:', error);
      throw error;
    }
  };

  const loadResults = async () => {
    try {
      await dispatch(fetchBacktestResults()).unwrap();
    } catch (error) {
      console.error('Failed to load backtest results:', error);
      throw error;
    }
  };

  const selectResult = (result: any) => {
    dispatch(selectBacktestResult(result));
  };

  return {
    results,
    currentResult,
    loading,
    error,
    executeBacktest,
    loadResults,
    selectResult,
  };
};
