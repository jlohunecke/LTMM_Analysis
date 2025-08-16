import React, { useState, useEffect } from 'react';
import Papa from 'papaparse';

const TimestampAnalysis = () => {
  const [data, setData] = useState([]);
  const [violations, setViolations] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadAndAnalyzeData = async () => {
      try {
        const csvData = await window.fs.readFile('complete_wear_periods_reformatted.csv', { encoding: 'utf8' });
        
        const parsed = Papa.parse(csvData, {
          header: true,
          skipEmptyLines: true,
          dynamicTyping: false,
          delimitersToGuess: [',', '\t', '|', ';'],
          transformHeader: (header) => header.trim()
        });

        const processedData = parsed.data.map(row => {
          const pigId = row.pig_id?.trim();
          const timestamps = [];
          
          // Extract all timestamps from the row
          Object.keys(row).forEach(key => {
            if (key.startsWith('wear_') && row[key] && row[key].trim()) {
              const timestamp = row[key].trim();
              const columnType = key.includes('start') ? 'start' : 'end';
              const periodNumber = key.match(/\d+/)?.[0] || '0';
              timestamps.push({
                value: timestamp,
                column: key,
                type: columnType,
                period: parseInt(periodNumber),
                date: new Date(timestamp)
              });
            }
          });
          
          // Sort timestamps by their order in the columns
          timestamps.sort((a, b) => {
            if (a.period !== b.period) return a.period - b.period;
            return a.type === 'start' ? -1 : 1;
          });
          
          return { pigId, timestamps };
        });

        setData(processedData);
        
        // Analyze violations
        const foundViolations = [];
        
        processedData.forEach(({ pigId, timestamps }) => {
          if (timestamps.length === 0) return;
          
          // Check condition 1: Later columns should have later timestamps
          for (let i = 1; i < timestamps.length; i++) {
            if (timestamps[i].date < timestamps[i-1].date) {
              foundViolations.push({
                pigId,
                type: 'chronological_order',
                description: `Timestamp in ${timestamps[i].column} (${timestamps[i].value}) is earlier than ${timestamps[i-1].column} (${timestamps[i-1].value})`
              });
            }
          }
          
          // Check condition 2: No two timestamps should be equal
          for (let i = 1; i < timestamps.length; i++) {
            if (timestamps[i].date.getTime() === timestamps[i-1].date.getTime()) {
              foundViolations.push({
                pigId,
                type: 'duplicate_timestamps',
                description: `Equal timestamps found: ${timestamps[i-1].column} and ${timestamps[i].column} both have ${timestamps[i].value}`
              });
            }
          }
          
          // Check condition 3: Last timestamp should be in a wear_end_x column
          if (timestamps.length > 0) {
            const lastTimestamp = timestamps[timestamps.length - 1];
            if (lastTimestamp.type !== 'end') {
              foundViolations.push({
                pigId,
                type: 'last_timestamp_not_end',
                description: `Last timestamp is in ${lastTimestamp.column} (should be wear_end_x)`
              });
            }
          }
        });
        
        setViolations(foundViolations);
        setLoading(false);
      } catch (error) {
        console.error('Error processing data:', error);
        setLoading(false);
      }
    };

    loadAndAnalyzeData();
  }, []);

  if (loading) {
    return <div className="p-4">Loading and analyzing data...</div>;
  }

  const violationsByType = violations.reduce((acc, v) => {
    acc[v.type] = (acc[v.type] || 0) + 1;
    return acc;
  }, {});

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Pig Wear Period Timestamp Analysis</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h3 className="font-semibold text-blue-800">Total Pigs</h3>
          <p className="text-2xl text-blue-600">{data.length}</p>
        </div>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <h3 className="font-semibold text-red-800">Total Violations</h3>
          <p className="text-2xl text-red-600">{violations.length}</p>
        </div>
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <h3 className="font-semibold text-green-800">Clean Pigs</h3>
          <p className="text-2xl text-green-600">{data.length - new Set(violations.map(v => v.pigId)).size}</p>
        </div>
      </div>

      <div className="mb-6">
        <h2 className="text-xl font-semibold mb-4">Violation Summary</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <h4 className="font-medium text-yellow-800">Chronological Order</h4>
            <p className="text-lg text-yellow-600">{violationsByType.chronological_order || 0}</p>
            <p className="text-sm text-yellow-700">Later columns with earlier timestamps</p>
          </div>
          <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
            <h4 className="font-medium text-orange-800">Duplicate Timestamps</h4>
            <p className="text-lg text-orange-600">{violationsByType.duplicate_timestamps || 0}</p>
            <p className="text-sm text-orange-700">Equal timestamps in same row</p>
          </div>
          <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
            <h4 className="font-medium text-purple-800">Last Not End</h4>
            <p className="text-lg text-purple-600">{violationsByType.last_timestamp_not_end || 0}</p>
            <p className="text-sm text-purple-700">Last timestamp not in wear_end_x</p>
          </div>
        </div>
      </div>

      {violations.length > 0 && (
        <div className="mb-6">
          <h2 className="text-xl font-semibold mb-4">Detailed Violations</h2>
          <div className="bg-white border rounded-lg overflow-hidden">
            <div className="max-h-96 overflow-y-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-50 sticky top-0">
                  <tr>
                    <th className="px-4 py-2 text-left">Pig ID</th>
                    <th className="px-4 py-2 text-left">Violation Type</th>
                    <th className="px-4 py-2 text-left">Description</th>
                  </tr>
                </thead>
                <tbody>
                  {violations.map((violation, index) => (
                    <tr key={index} className={index % 2 === 0 ? 'bg-gray-50' : 'bg-white'}>
                      <td className="px-4 py-2 font-mono">{violation.pigId}</td>
                      <td className="px-4 py-2">
                        <span className={`px-2 py-1 rounded text-xs ${
                          violation.type === 'chronological_order' ? 'bg-yellow-100 text-yellow-800' :
                          violation.type === 'duplicate_timestamps' ? 'bg-orange-100 text-orange-800' :
                          'bg-purple-100 text-purple-800'
                        }`}>
                          {violation.type.replace('_', ' ').toUpperCase()}
                        </span>
                      </td>
                      <td className="px-4 py-2">{violation.description}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      <div className="bg-gray-50 border rounded-lg p-4">
        <h3 className="font-semibold mb-2">Analysis Summary</h3>
        <div className="text-sm space-y-1">
          <p><strong>Condition 1:</strong> Timestamps in later columns should be chronologically after earlier columns</p>
          <p><strong>Condition 2:</strong> No two timestamps in a row should be equal</p>
          <p><strong>Condition 3:</strong> The last timestamp in each row should be in a wear_end_x column</p>
        </div>
      </div>
    </div>
  );
};

export default TimestampAnalysis;