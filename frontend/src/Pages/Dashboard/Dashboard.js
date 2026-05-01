import React from 'react';
import './Dashboard.css';

function Dashboard() {
  return (
    <div className="dashboard-container">
      <h1 className="text-3xl font-bold mb-6">BLETrack Dashboard</h1>
      <div className="card bg-base-200 shadow-xl">
        <div className="card-body">
          <h2 className="card-title">Current Devices</h2>
          <div className="overflow-x-auto">
            <table className="table table-zebra w-full">
              <thead>
                <tr>
                  <th>Public Name</th>
                  <th>Device Type</th>
                  <th>Status</th>
                  <th>Room</th>
                  <th>Distance</th>
                  <th>Last Seen</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td colSpan="6" className="text-center text-gray-500">
                    Loading devices...
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
