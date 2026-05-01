import { apiGet } from './index';

export async function fetchLatestPresence(params = {}) {
  const qs = new URLSearchParams();
  if (params.limit) qs.set('limit', String(params.limit));
  if (params.room) qs.set('room', params.room);
  if (params.device_id) qs.set('device_id', params.device_id);
  if (params.alias) qs.set('alias', params.alias);
  if (params.paired_only) qs.set('paired_only', 'true');
  const query = qs.toString();
  return apiGet(`/presence/latest${query ? '?' + query : ''}`);
}

export async function fetchPresenceHistory(params = {}) {
  const qs = new URLSearchParams();
  if (params.minutes) qs.set('minutes', String(params.minutes));
  if (params.limit) qs.set('limit', String(params.limit));
  if (params.room) qs.set('room', params.room);
  if (params.device_id) qs.set('device_id', params.device_id);
  if (params.alias) qs.set('alias', params.alias);
  if (params.paired_only) qs.set('paired_only', 'true');
  const query = qs.toString();
  return apiGet(`/presence/history${query ? '?' + query : ''}`);
}
