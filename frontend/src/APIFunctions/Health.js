import { apiGet } from './index';

export async function fetchHealth() {
  return apiGet('/health');
}
