import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import DatePicker from 'react-datepicker';
import Select from 'react-select';
import 'react-datepicker/dist/react-datepicker.css';
import { api } from '../services/api';

interface StrategyOption {
  value: string;
  label: string;
  parameters?: { [key: string]: unknown };
}

const Backtester: React.FC = () => {
  const navigate = useNavigate();
  const [startDate, setStartDate] = useState<Date | null>(new Date('2023-01-01'));
  const [endDate, setEndDate] = useState<Date | null>(new Date());
  const [strategy, setStrategy] = useState<StrategyOption | null>(null);
  const [symbol, setSymbol] = useState<string>('');
  const [parameters, setParameters] = useState<{ [key: string]: unknown }>({});
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isParamsLoading, setIsParamsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [strategyOptions, setStrategyOptions] = useState<StrategyOption[]>([]);

  useEffect(() => {
    const fetchStrategies = async () => {
      setIsParamsLoading(true);
      try {
        const strategies = await api.getStrategies();
        setStrategyOptions(strategies.map((strategy) => ({
          value: strategy.name,
          label: strategy.name,
          parameters: strategy.parameters
        })));
      } catch (error) {
        console.error('Error fetching strategies:', error);
        setError('Failed to load strategies.');
      } finally {
        setIsParamsLoading(false);
      }
    };

    fetchStrategies();
  }, []);

  const handleParameterChange = (key: string, value: unknown) => {
    setParameters(prev => ({ ...prev, [key]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    try {
      const results = await api.runBacktest({
        strategy: strategy?.value,
        params: parameters,
        startDate: startDate?.toISOString(),
        endDate: endDate?.toISOString(),
        symbol: symbol,
      });
      navigate('/results', { state: { results } });
    } catch (error) {
      console.error('Error running backtest:', error);
      setError('An error occurred while running the backtest. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-3xl font-bold mb-6">Backtester</h1>
      <form onSubmit={handleSubmit} className="bg-white shadow-md rounded px-8 pt-6 pb-8 mb-4">
        <div className="mb-4">
          <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="strategy">
            Strategy
          </label>
          <Select
            id="strategy"
            options={strategyOptions}
            value={strategy}
            onChange={setStrategy}
            className="w-full"
          />
        </div>
        <div className="mb-4">
          <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="symbol">
            Symbol
          </label>
          <input
            className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
            id="symbol"
            type="text"
            placeholder="Enter symbol (e.g., AAPL)"
            value={symbol}
            onChange={(e) => setSymbol(e.target.value)}
          />
        </div>
        <div className="mb-4 flex space-x-4">
          <div className="w-1/2">
            <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="startDate">
              Start Date
            </label>
            <DatePicker
              selected={startDate}
              onChange={(date) => setStartDate(date)}
              className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
            />
          </div>
          <div className="w-1/2">
            <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="endDate">
              End Date
            </label>
            <DatePicker
              selected={endDate}
              onChange={(date) => setEndDate(date)}
              className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
            />
          </div>
        </div>
        {strategy && (
          <div className="mb-4">
            <h3 className="text-lg font-semibold mb-2">Strategy Parameters</h3>
            {isParamsLoading ? (
              <p>Loading parameters...</p>
            ) : (
              strategy.parameters && Object.entries(strategy.parameters).map(([key, param]) => (
                <ParameterInput
                  key={key}
                  label={key}
                  value={(parameters[key] || '') as string | number}
                  onChange={(value) => handleParameterChange(key, value)}
                  type={typeof param === 'number' ? 'number' : 'text'}
                />
              ))
            )}
          </div>
        )}
        {error && <p className="text-red-500 mb-4">{error}</p>}
        <div className="flex items-center justify-between">
          <button
            className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline"
            type="submit"
            disabled={isLoading}
          >
            {isLoading ? 'Running...' : 'Run Backtest'}
          </button>
        </div>
      </form>
    </div>
  );
};

const ParameterInput: React.FC<{ label: string; value: string | number; onChange: (value: unknown) => void; type: string }> = ({ label, value, onChange, type }) => (
  <div className="mb-2">
    <label className="block text-gray-700 text-sm font-bold mb-2">
      {label}
    </label>
    <input
      className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
      type={type}
      value={value}
      onChange={(e) => onChange(e.target.value)}
    />
  </div>
);

export default Backtester;
