import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const Comparison: React.FC = () => {
  // Sample data - replace with actual comparison data
  const comparisonData = [
    { name: 'Total Return', strategy1: 15.2, strategy2: 12.8, benchmark: 10.5 },
    { name: 'Sharpe Ratio', strategy1: 1.8, strategy2: 1.5, benchmark: 1.2 },
    { name: 'Max Drawdown', strategy1: -8.5, strategy2: -10.2, benchmark: -12.5 },
    { name: 'Profit Factor', strategy1: 2.3, strategy2: 2.1, benchmark: 1.8 },
  ];

  return (
    <div>
      <h1 className="text-3xl font-bold mb-6">Strategy Comparison</h1>
      
      <div className="mb-8">
        <h2 className="text-2xl font-semibold mb-4">Performance Metrics</h2>
        <div className="bg-white p-4 rounded-lg shadow" style={{ height: '400px' }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={comparisonData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="strategy1" fill="#8884d8" name="Strategy 1" />
              <Bar dataKey="strategy2" fill="#82ca9d" name="Strategy 2" />
              <Bar dataKey="benchmark" fill="#ffc658" name="Benchmark" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="mb-8">
        <h2 className="text-2xl font-semibold mb-4">Detailed Comparison</h2>
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Metric</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Strategy 1</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Strategy 2</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Benchmark</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {comparisonData.map((item) => (
                <tr key={item.name}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{item.name}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{item.strategy1}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{item.strategy2}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{item.benchmark}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="mt-8">
        <h2 className="text-2xl font-semibold mb-4">Analysis</h2>
        <div className="bg-white p-6 rounded-lg shadow">
          <p className="text-gray-700 mb-4">
            Based on the comparison above, Strategy 1 outperforms both Strategy 2 and the benchmark across all key metrics. It shows a higher total return, better risk-adjusted performance (Sharpe ratio), lower maximum drawdown, and a higher profit factor.
          </p>
          <p className="text-gray-700 mb-4">
            Strategy 2, while not as strong as Strategy 1, still outperforms the benchmark. This suggests that both strategies have merit, but Strategy 1 appears to be the superior choice based on historical backtesting results.
          </p>
          <p className="text-gray-700">
            It's important to note that past performance doesn't guarantee future results. Consider running additional tests with different time periods and market conditions to ensure the robustness of these strategies.
          </p>
        </div>
      </div>
    </div>
  );
};

export default Comparison;