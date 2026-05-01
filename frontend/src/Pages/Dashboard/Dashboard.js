import React, { useEffect, useState } from 'react';
import { fetchCurrentDevices } from '../../APIFunctions/Device';
import './Dashboard.css';

function Dashboard() {
  const [devices, setDevices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastRefreshed, setLastRefreshed] = useState(null);

  async function loadDevices() {
    try {
      setLoading(true);
      setError(null);
      const data = await fetchCurrentDevices();
      setDevices(data.data || []);
      setLastRefreshed(new Date());
    } catch (err) {
      setError(err.message || 'Failed to fetch devices');
      setDevices([]);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadDevices();
    const interval = setInterval(loadDevices, 10000);
    return () => clearInterval(interval);
  }, []);

  function safe(v) {
    return v === null || v === undefined || v === '' ? '-' : String(v);
  }

  function fmtTs(ts) {
    if (!ts) return '-';
    const d = new Date(ts);
    if (Number.isNaN(d.getTime())) return ts;
    return d.toLocaleString();
  }

  return (
    <div className="dashboard-container">
      <h1 className="text-4xl font-bold mb-2">BLETrack Dashboard</h1>
      <p className="text-gray-400 mb-6">
        Monitor paired BLE devices in real-time.
      </p>

      <div className="sce-card p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-semibold">Current Devices</h2>
          {lastRefreshed && (
            <span className="text-sm text-gray-500">
              Last refreshed: {lastRefreshed.toLocaleTimeString()}
            </span>
          )}
        </div>

        {error ? (
          <div className="text-center py-12">
            <div className="text-red-400 text-lg font-semibold mb-2">
              Database Unreachable
            </div>
            <p className="text-gray-500">{error}</p>
            <button
              onClick={loadDevices}
              className="sce-btn-primary mt-4"
            >
              Retry
            </button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="table w-full">
              <thead>
                <tr className="border-b border-base-300">
                  <th className="text-left py-3 px-4 text-gray-400 font-semibold">Public Name</th>
                  <th className="text-left py-3 px-4 text-gray-400 font-semibold">Device Type</th>
                  <th className="text-left py-3 px-4 text-gray-400 font-semibold">Status</th>
                  <th className="text-left py-3 px-4 text-gray-400 font-semibold">Room</th>
                  <th className="text-left py-3 px-4 text-gray-400 font-semibold">Distance</th>
                  <th className="text-left py-3 px-4 text-gray-400 font-semibold">Last Seen</th>
                </tr>
              </thead>
              <tbody>
                {loading && devices.length === 0 ? (
                  <tr>
                    <td colSpan="6" className="text-center py-12">
                      <span className="loading loading-spinner loading-lg text-primary"></span>
                      <p className="text-gray-500 mt-3">Loading devices...</p>
                    </td>
                  </tr>
                ) : devices.length === 0 ? (
                  <tr>
                    <td colSpan="6" className="text-center py-12 text-gray-500">
                      No paired devices found.
                    </td>
                  </tr>
                ) : (
                  devices.map((device, idx) => (
                    <tr
                      key={idx}
                      className="border-b border-base-300 hover:bg-base-300 transition-colors"
                    >
                      <td className="py-3 px-4 font-medium">{safe(device.public_name)}</td>
                      <td className="py-3 px-4">
                        <span className="badge badge-outline">{safe(device.device_type)}</span>
                      </td>
                      <td className="py-3 px-4">
                        {device.is_online ? (
                          <span className="badge badge-success gap-1">
                            <span className="w-2 h-2 rounded-full bg-green-300"></span>
                            online
                          </span>
                        ) : (
                          <span className="badge badge-ghost gap-1">
                            <span className="w-2 h-2 rounded-full bg-gray-500"></span>
                            offline
                          </span>
                        )}
                      </td>
                      <td className="py-3 px-4">{safe(device.room)}</td>
                      <td className="py-3 px-4">
                        {device.distance_m != null ? `${Number(device.distance_m).toFixed(2)}m` : '-'}
                      </td>
                      <td className="py-3 px-4 text-gray-400">{fmtTs(device.last_seen_ts)}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

export default Dashboard;
