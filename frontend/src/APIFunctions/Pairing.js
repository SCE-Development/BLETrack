import { apiGet, apiPost } from './index';

export async function startEnrollment(deviceType = 'phone', name = 'new_device') {
  return apiGet(`/enroll/start?device_type=${encodeURIComponent(deviceType)}&name=${encodeURIComponent(name)}`);
}

export async function cancelEnrollment() {
  return apiGet('/enroll/cancel');
}

export async function fetchPairCandidates(limit = 200) {
  return apiGet(`/pair/candidates?limit=${limit}`);
}

export async function finalizePairing(payload) {
  return apiPost('/pair/finalize', payload);
}

export async function removePairedDevice(publicName) {
  return apiPost('/pair/remove', { public_name: publicName });
}
