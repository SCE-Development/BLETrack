import { apiGet, apiPost } from './index';

export async function fetchCurrentDevices(limit = 500) {
  return apiGet(`/dashboard/current?limit=${limit}`);
}

export async function fetchManagedDevices(limit = 500) {
  return apiGet(`/devices/managed?limit=${limit}`);
}

export async function fetchDiscoveredDevices(limit = 500) {
  return apiGet(`/devices/discovered?limit=${limit}`);
}

export async function upsertManagedDevice(payload) {
  return apiPost('/devices/managed', payload);
}
