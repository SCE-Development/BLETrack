import React, { useEffect, useState } from 'react';
import { fetchManagedDevices, fetchDiscoveredDevices } from '../../APIFunctions/Device';

function Devices() {
  const [managed, setManaged] = useState([]);
  const [discovered, setDiscovered] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('managed');

  async function loadData() {
    try {
      setLoading(true);
      setError(null);
      const [managedRes, discoveredRes] = await Promise.all([
        fetchManagedDevices(),
        fetchDiscoveredDevices(),
      ]);
      setManaged(managedRes.data || []);
      setDiscovered(discoveredRes.data || []);
    } catch (err) {
      setError(err.message || 'Failed to fetch devices');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
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
    <div className="devices-container">
      <h1 className="text-4xl font-bold mb-2">Devices</h1>
      <p className="text-gray-400 mb-6">
        View all managed and discovered BLE devices.
      </p>

      <div className="tabs tabs-boxed bg-base-200 mb-6 inline-flex">
        <button
          className={`tab ${activeTab === 'managed' ? 'tab-active bg-blue-500 text-white' : 'text-gray-400'}`}
          onClick={() => setActiveTab('managed')}
        >
          Managed ({managed.length})
        </button>
        <button
          className={`tab ${activeTab === 'discovered' ? 'tab-active bg-blue-500 text-white' : 'text-gray-400'}`}
          onClick={() => setActiveTab('discovered')}
        >
          Discovered ({discovered.length})
        </button>
      </div>

      <div className="sce-card p-6">
        {error ? (
          <div className="text-center py-12">
            <div className="text-red-400 text-lg font-semibold mb-2">Database Unreachable</div>
            <p className="text-gray-500">{error}</p>
            <button onClick={loadData} className="sce-btn-primary mt-4">Retry</button>
          </div>
        ) : loading ? (
          <div className="text-center py-12">
            <span className="loading loading-spinner loading-lg text-primary"></span>
            <p className="text-gray-500 mt-3">Loading devices...</p>
          </div>
        ) : activeTab === 'managed' ? (
          <div className="overflow-x-auto">
            <table className="table w-full">
              <thead>
                <tr className="border-b border-base-300">
                  <th className="text-left py-3 px-4 text-gray-400 font-semibold">Display Name</th>
                  <th className="text-left py-3 px-4 text-gray-400 font-semibold">Type</th>
                  <th className="text-left py-3 px-4 text-gray-400 font-semibold">Observed ID</th>
                  <th className="text-left py-3 px-4 text-gray-400 font-semibold">Fingerprint ID</th>
                  <th className="text-left py-3 px-4 text-gray-400 font-semibold">Active</th>
                  <th className="text-left py-3 px-4 text-gray-400 font-semibold">Last Seen</th>
                </tr>
              </thead>
              <tbody>
                {managed.length === 0 ? (
                  <tr>
                    <td colSpan="6" className="text-center py-12 text-gray-500">
                      No managed devices found.
                    </td>
                  </tr>
                ) : (
                  managed.map((device, idx) => (
                    <tr key={idx} className="border-b border-base-300 hover:bg-base-300 transition-colors">
                      <td className="py-3 px-4 font-medium">{safe(device.display_name)}</td>
                      <td className="py-3 px-4">
                        <span className="badge badge-outline">{safe(device.device_type)}</span>
                      </td>
                      <td className="py-3 px-4 font-mono text-sm">{safe(device.observed_device_id)}</td>
                      <td className="py-3 px-4 font-mono text-sm">{safe(device.fingerprint_device_id)}</td>
                      <td className="py-3 px-4">
                        {device.is_active ? (
                          <span className="badge badge-success">active</span>
                        ) : (
                          <span className="badge badge-ghost">inactive</span>
                        )}
                      </td>
                      <td className="py-3 px-4 text-gray-400">{fmtTs(device.last_seen_ts)}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="table w-full">
              <thead>
                <tr className="border-b border-base-300">
                  <th className="text-left py-3 px-4 text-gray-400 font-semibold">Device ID</th>
                  <th className="text-left py-3 px-4 text-gray-400 font-semibold">Discovered Name</th>
                  <th className="text-left py-3 px-4 text-gray-400 font-semibold">Room</th>
                  <th className="text-left py-3 px-4 text-gray-400 font-semibold">Distance</th>
                  <th className="text-left py-3 px-4 text-gray-400 font-semibold">RSSI</th>
                  <th className="text-left py-3 px-4 text-gray-400 font-semibold">Last Seen</th>
                </tr>
              </thead>
              <tbody>
                {discovered.length === 0 ? (
                  <tr>
                    <td colSpan="6" className="text-center py-12 text-gray-500">
                      No discovered devices found.
                    </td>
                  </tr>
                ) : (
                  discovered.map((device, idx) => (
                    <tr key={idx} className="border-b border-base-300 hover:bg-base-300 transition-colors">
                      <td className="py-3 px-4 font-mono text-sm">{safe(device.device_id)}</td>
                      <td className="py-3 px-4">{safe(device.discovered_name)}</td>
                      <td className="py-3 px-4">{safe(device.room)}</td>
                      <td className="py-3 px-4">
                        {device.distance_m != null ? `${Number(device.distance_m).toFixed(2)}m` : '-'}
                      </td>
                      <td className="py-3 px-4">{device.rssi != null ? `${device.rssi} dBm` : '-'}</td>
                      <td className="py-3 px-4 text-gray-400">{fmtTs(device.ts)}</td>
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

export default Devices;
