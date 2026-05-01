import { apiGet } from './index';

export async function fetchCurrentDevices(limit = 500) {
  return apiGet(`/dashboard/current?limit=${limit}`);
}
