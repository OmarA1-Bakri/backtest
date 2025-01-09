import React from 'react';
import { BarChart2, TrendingUp, TrendingDown, DollarSign } from 'lucide-react';

const Dashboard: React.FC = () => {
  return (
    <div>
      <h1 className="text-3xl font-bold mb-6 text-gray-900 dark:text-white">Dashboard</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard title="Total Return" value="15.2%" icon={<TrendingUp />} color="text-green-500" />
        <StatCard title="Sharpe Ratio" value="1.8" icon={<BarChart2 />} color="text-blue-500" />
        <StatCard title="Max Drawdown" value="-8.5%" icon={<TrendingDown />} color="text-red-500" />
        <StatCard title="Profit Factor" value="2.3" icon={<DollarSign />} color="text-yellow-500" />
      </div>
      <div className="mt-8">
        <h2 className="text-2xl font-semibold mb-4 text-gray-800 dark:text-white">Recent Backtests</h2>
        <div className="bg-white dark:bg-gray-800 shadow rounded-lg overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
            <thead className="bg-gray-50 dark:bg-gray-700">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Strategy</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Date</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Return</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Sharpe Ratio</th>
              </tr>
            </thead>
            <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
              <TableRow strategy="Moving Average Crossover" date="2024-03-15" return="8.5%" sharpeRatio="1.6" />
              <TableRow strategy="RSI Oscillator" date="2024-03-14" return="6.2%" sharpeRatio="1.4" />
              <TableRow strategy="MACD Divergence" date="2024-03-13" return="7.8%" sharpeRatio="1.5" />
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

const StatCard: React.FC<{ title: string; value: string; icon: React.ReactNode; color: string }> = ({ title, value, icon, color }) => (
  <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
    <div className="flex items-center">
      <div className={`p-3 rounded-full ${color} bg-opacity-10 mr-4`}>
        {icon}
      </div>
      <div>
        <p className="text-sm font-medium text-gray-500 dark:text-gray-400">{title}</p>
        <p className="text-2xl font-semibold text-gray-900 dark:text-white">{value}</p>
      </div>
    </div>
  </div>
);

const TableRow: React.FC<{ strategy: string; date: string; return: string; sharpeRatio: string }> = ({ strategy, date, return: returnValue, sharpeRatio }) => (
  <tr>
    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">{strategy}</td>
    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-300">{date}</td>
    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-300">{returnValue}</td>
    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-300">{sharpeRatio}</td>
  </tr>
);

export default Dashboard;