import React, { useEffect, useState } from 'react';
import {
  startEnrollment,
  cancelEnrollment,
  fetchPairCandidates,
  finalizePairing,
  removePairedDevice,
} from '../../APIFunctions/Pairing';
import { fetchCurrentDevices } from '../../APIFunctions/Device';

function Pairing() {
  const [enrolling, setEnrolling] = useState(false);
  const [enrollMsg, setEnrollMsg] = useState('');
  const [candidates, setCandidates] = useState([]);
  const [pairedDevices, setPairedDevices] = useState([]);
  const [fingerprints, setFingerprints] = useState([]);
  const [loading, setLoading] = useState(true);

  const [publicName, setPublicName] = useState('');
  const [deviceType, setDeviceType] = useState('phone');
  const [fingerprintId, setFingerprintId] = useState('');
  const [observedId, setObservedId] = useState('');
  const [pairMsg, setPairMsg] = useState('');

  async function loadData() {
    try {
      setLoading(true);
      const [candidatesRes, devicesRes] = await Promise.all([
        fetchPairCandidates(),
        fetchCurrentDevices(),
      ]);
      setCandidates(candidatesRes.data || []);
      setPairedDevices(devicesRes.data || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  async function handleStartEnroll() {
    setEnrollMsg('Starting enrollment...');
    try {
      await startEnrollment(deviceType, publicName || 'new_device');
      setEnrolling(true);
      setEnrollMsg('Enrollment started. Pair on your device, then refresh candidates.');
    } catch (err) {
      setEnrollMsg(`Failed: ${err.message}`);
    }
  }

  async function handleCancelEnroll() {
    setEnrollMsg('Canceling enrollment...');
    try {
      await cancelEnrollment();
      setEnrolling(false);
      setEnrollMsg('Enrollment canceled.');
    } catch (err) {
      setEnrollMsg(`Failed: ${err.message}`);
    }
  }

  async function handlePair() {
    if (!publicName) {
      setPairMsg('Public Name is required.');
      return;
    }
    if (!fingerprintId && !observedId) {
      setPairMsg('Select a Fingerprint ID or Live Device ID.');
      return;
    }

    setPairMsg('Pairing device...');
    try {
      await finalizePairing({
        public_name: publicName,
        device_type: deviceType,
        fingerprint_device_id: fingerprintId || null,
        observed_device_id: observedId || null,
      });
      setPairMsg('Device paired successfully.');
      setPublicName('');
      setFingerprintId('');
      setObservedId('');
      await loadData();
    } catch (err) {
      setPairMsg(`Pair failed: ${err.message}`);
    }
  }

  async function handleRemove(name) {
    try {
      await removePairedDevice(name);
      await loadData();
    } catch (err) {
      console.error(err);
    }
  }

  return (
    <div className="pairing-container">
      <h1 className="text-4xl font-bold mb-2">Device Pairing</h1>
      <p className="text-gray-400 mb-6">
        Enroll new devices and manage existing pairings.
      </p>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Enrollment */}
        <div className="sce-card p-6">
          <h2 className="text-2xl font-semibold mb-4">Enrollment Mode</h2>
          <div className="flex gap-4 mb-4">
            <select
              className="select select-bordered bg-base-300 flex-1"
              value={deviceType}
              onChange={(e) => setDeviceType(e.target.value)}
            >
              <option value="phone">phone</option>
              <option value="watch">watch</option>
              <option value="tablet">tablet</option>
              <option value="other">other</option>
            </select>
            <input
              type="text"
              placeholder="Device name"
              className="input input-bordered bg-base-300 flex-1"
              value={publicName}
              onChange={(e) => setPublicName(e.target.value)}
            />
          </div>
          <div className="flex gap-3">
            <button
              onClick={handleStartEnroll}
              className="sce-btn-primary"
              disabled={enrolling}
            >
              Start Enrollment
            </button>
            <button
              onClick={handleCancelEnroll}
              className="sce-btn-secondary"
              disabled={!enrolling}
            >
              Cancel Enrollment
            </button>
          </div>
          {enrollMsg && (
            <p className={`mt-3 text-sm ${enrollMsg.includes('Failed') ? 'text-red-400' : 'text-green-400'}`}>
              {enrollMsg}
            </p>
          )}
        </div>

        {/* Pairing Form */}
        <div className="sce-card p-6">
          <h2 className="text-2xl font-semibold mb-4">Finalize Pairing</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            <input
              type="text"
              placeholder="Public Name *"
              className="input input-bordered bg-base-300"
              value={publicName}
              onChange={(e) => setPublicName(e.target.value)}
            />
            <select
              className="select select-bordered bg-base-300"
              value={deviceType}
              onChange={(e) => setDeviceType(e.target.value)}
            >
              <option value="phone">phone</option>
              <option value="watch">watch</option>
              <option value="tablet">tablet</option>
              <option value="other">other</option>
            </select>
            <select
              className="select select-bordered bg-base-300"
              value={fingerprintId}
              onChange={(e) => setFingerprintId(e.target.value)}
            >
              <option value="">Select Fingerprint ID</option>
              {candidates
                .filter((c) => c.observed_device_id && c.observed_device_id.includes(':'))
                .map((c) => (
                  <option key={c.observed_device_id} value={c.observed_device_id}>
                    {c.observed_device_id}
                  </option>
                ))}
            </select>
            <select
              className="select select-bordered bg-base-300"
              value={observedId}
              onChange={(e) => setObservedId(e.target.value)}
            >
              <option value="">Select Live Device ID</option>
              {candidates.map((c) => (
                <option key={c.observed_device_id} value={c.observed_device_id}>
                  {c.observed_device_id} {c.live_name ? `(${c.live_name})` : ''}
                </option>
              ))}
            </select>
          </div>
          <button onClick={handlePair} className="sce-btn-primary">
            Pair Device
          </button>
          {pairMsg && (
            <p className={`mt-3 text-sm ${pairMsg.includes('Failed') || pairMsg.includes('required') ? 'text-red-400' : 'text-green-400'}`}>
              {pairMsg}
            </p>
          )}
        </div>
      </div>

      {/* Paired Devices */}
      <div className="sce-card p-6 mt-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-semibold">Paired Devices</h2>
          <button onClick={loadData} className="sce-btn-secondary">
            Refresh
          </button>
        </div>
        {loading ? (
          <div className="text-center py-8">
            <span className="loading loading-spinner loading-md text-primary"></span>
          </div>
        ) : pairedDevices.length === 0 ? (
          <p className="text-gray-500 text-center py-8">No paired devices yet.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="table w-full">
              <thead>
                <tr className="border-b border-base-300">
                  <th className="text-left py-3 px-4 text-gray-400 font-semibold">Public Name</th>
                  <th className="text-left py-3 px-4 text-gray-400 font-semibold">Type</th>
                  <th className="text-left py-3 px-4 text-gray-400 font-semibold">Status</th>
                  <th className="text-left py-3 px-4 text-gray-400 font-semibold">Room</th>
                  <th className="text-left py-3 px-4 text-gray-400 font-semibold">Action</th>
                </tr>
              </thead>
              <tbody>
                {pairedDevices.map((device, idx) => (
                  <tr key={idx} className="border-b border-base-300 hover:bg-base-300 transition-colors">
                    <td className="py-3 px-4 font-medium">{device.public_name || '-'}</td>
                    <td className="py-3 px-4">
                      <span className="badge badge-outline">{device.device_type || '-'}</span>
                    </td>
                    <td className="py-3 px-4">
                      {device.is_online ? (
                        <span className="badge badge-success">online</span>
                      ) : (
                        <span className="badge badge-ghost">offline</span>
                      )}
                    </td>
                    <td className="py-3 px-4">{device.room || '-'}</td>
                    <td className="py-3 px-4">
                      <button
                        onClick={() => handleRemove(device.public_name)}
                        className="btn btn-sm btn-error btn-outline"
                      >
                        Remove
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

export default Pairing;
