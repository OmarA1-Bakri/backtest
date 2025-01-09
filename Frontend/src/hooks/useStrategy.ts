import { useDispatch, useSelector } from 'react-redux';
import {
  fetchStrategies,
  saveStrategy,
  selectStrategy,
  selectStrategies,
  selectCurrentStrategy,
  selectStrategyLoading,
  selectStrategyError,
} from '../store/slices/strategySlice';
import { AppDispatch } from '../store/store';

export const useStrategy = () => {
  const dispatch = useDispatch<AppDispatch>();
  const strategies = useSelector(selectStrategies);
  const currentStrategy = useSelector(selectCurrentStrategy);
  const loading = useSelector(selectStrategyLoading);
  const error = useSelector(selectStrategyError);

  const loadStrategies = async () => {
    try {
      await dispatch(fetchStrategies()).unwrap();
    } catch (error) {
      console.error('Failed to load strategies:', error);
      throw error;
    }
  };

  const createStrategy = async (strategyData: {
    name: string;
    description: string;
    params: Record<string, any>;
  }) => {
    try {
      const result = await dispatch(saveStrategy(strategyData)).unwrap();
      return result;
    } catch (error) {
      console.error('Failed to create strategy:', error);
      throw error;
    }
  };

  const selectCurrentStrategyById = (strategyId: string) => {
    const strategy = strategies.find((s) => s.id === strategyId);
    if (strategy) {
      dispatch(selectStrategy(strategy));
    }
  };

  return {
    strategies,
    currentStrategy,
    loading,
    error,
    loadStrategies,
    createStrategy,
    selectStrategy: selectCurrentStrategyById,
  };
};
