import { useEffect, useState } from 'react';

const API_URL = import.meta.env.VITE_API_URL ?? 'http://127.0.0.1:8000';

function App() {
  const [health, setHealth] = useState('...');

  useEffect(() => {
    async function checkHealth() {
      try {
        const response = await fetch(`${API_URL}/health`);
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }
        const data = await response.json();
        setHealth(data.status ?? 'ok');
      } catch (error) {
        setHealth('offline');
        console.error('Error al consultar el backend', error);
      }
    }

    checkHealth();
  }, []);

  return (
    <main className="app-shell">
      <header>
        <h1>Florería Carlitos</h1>
        <p className="tagline">Panel de control en Electron + React</p>
      </header>
      <section className="status-card">
        <h2>Estado del backend</h2>
        <p className={`status status-${health}`}>{health}</p>
        <small>
          Edita <code>desktop_app/dev_backend.py</code> y los componentes de React para comenzar a
          desarrollar.
        </small>
      </section>
    </main>
  );
}

export default App;
