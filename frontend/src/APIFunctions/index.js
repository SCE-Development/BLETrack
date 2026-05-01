const BASE_API_URL = process.env.REACT_APP_BASE_API_URL || 'http://localhost:5055';

async function apiGet(path) {
  const res = await fetch(`${BASE_API_URL}${path}`);
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json();
}

async function apiPost(path, body) {
  const res = await fetch(`${BASE_API_URL}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json();
}

export { BASE_API_URL, apiGet, apiPost };
