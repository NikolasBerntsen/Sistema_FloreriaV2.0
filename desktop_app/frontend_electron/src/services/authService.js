const API_URL = import.meta.env.VITE_API_URL ?? 'http://127.0.0.1:8000';

function buildError(message, status) {
  const error = new Error(message);
  error.status = status;
  return error;
}

export async function login(credentials) {
  try {
    const response = await fetch(`${API_URL}/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(credentials),
    });

    const payload = await response.json().catch(() => null);

    if (!response.ok) {
      const detail = payload?.detail ?? 'Credenciales inválidas.';
      throw buildError(detail, response.status);
    }

    return payload;
  } catch (error) {
    if (error.name === 'TypeError') {
      throw buildError('No pudimos contactar al servidor. Intenta más tarde.', 'NETWORK');
    }
    throw error;
  }
}
