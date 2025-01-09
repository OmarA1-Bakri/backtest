import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { useTable } from 'react-table';
import jsPDF from 'jspdf'
import 'jspdf-autotable';
import { api } from '../services/api';

interface Trade {
  date: string;
  type: string;
  price: number;
  quantity: number;
}

interface PerformanceMetrics {
  [key: string]: number | string;
}

const Results: React.FC = () => {
  const [results, setResults] = useState<any>(null);
  const [metrics, setMetrics] = useState<PerformanceMetrics | null>(null);
  const location = useLocation();

  useEffect(() => {
    const fetchResults = async () => {
      if (location.state?.results) {
        setResults(location.state.results);
        try {
          const performanceMetrics = await api.getPerformanceMetrics(
            location.state.results.returns,
            location.state.results.trades
          );
          setMetrics(performanceMetrics);
        } catch (error) {
          console.error('Error fetching performance metrics:', error);
        }
      }
    };
    fetchResults();
  }, [location.state]);

  const columns = React.useMemo(
    () => [
      { Header: 'Date', accessor: 'date' },
      { Header: 'Type', accessor: 'type' },
      { Header: 'Price', accessor: 'price' },
      { Header: 'Quantity', accessor: 'quantity' },
    ],
    []
  );

  const {
    getTableProps,
    getTableBodyProps,
    headerGroups,
    rows,
    prepareRow,
  } = useTable({ columns, data: results?.trades || [] });

  const exportPDF = () => {
    const doc = new jsPDF();
    doc.text("Backtest Results", 14, 15);
    (doc as any).autoTable({
      head: [['Date', 'Type', 'Price', 'Quantity']],
      body: results?.trades.map((trade: Trade) => [trade.date, trade.type, trade.price, trade.quantity]),
    });
    doc.save("backtest-results.pdf");
  };

  if (!results || !metrics) {
    return <div>Loading...</div>;
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-6">Backtest Results</h1>
      
      <div className="mb-8">
        <h2 className="text-2xl font-semibold mb-4">Performance Chart</h2>
        <div className="bg-white p-4 rounded-lg shadow" style={{ height: '400px' }}>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={results.equity_curve}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="equity" stroke="#8884d8" activeDot={{ r: 8 }} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="mb-8">
        <h2 className="text-2xl font-semibold mb-4">Performance Metrics</h2>
        <div className="bg-white p-4 rounded-lg shadow">
          <table className="min-w-full divide-y divide-gray-200">
            <tbody>
              {Object.entries(metrics).map(([key, value]) => (
                <tr key={key}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{key}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{value}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="mb-8">
        <h2 className="text-2xl font-semibold mb-4">Trade Log</h2>
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table {...getTableProps()} className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              {headerGroups.map(headerGroup => (
                <tr {...headerGroup.getHeaderGroupProps()}>
                  {headerGroup.headers.map(column => (
                    <th
                      {...column.getHeaderProps()}
                      className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                    >
                      {column.render('Header')}
                    </th>
                  ))}
                </tr>
              ))}
            </thead>
            <tbody {...getTableBodyProps()} className="bg-white divide-y divide-gray-200">
              {rows.map(row => {
                prepareRow(row);
                return (
                  <tr {...row.getRowProps()}>
                    {row.cells.map(cell => (
                      <td
                        {...cell.getCellProps()}
                        className="px-6 py-4 whitespace-nowrap text-sm text-gray-500"
                      >
                        {cell.render('Cell')}
                      </td>
                    ))}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      <div className="mt-4">
        <button
          onClick={exportPDF}
          className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline"
        >
          Export PDF
        </button>
      </div>
    </div>
  );
};

export default Results;