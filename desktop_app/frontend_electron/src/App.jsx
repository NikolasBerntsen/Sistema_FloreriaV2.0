import { useState } from 'react';
import MainLayout from './layouts/MainLayout';
import LoginView from './views/Login/LoginView';

const QUICK_LOGIN_USER = {
  full_name: 'Equipo de Desarrollo',
  role: 'Administrador (dev)',
  permissions: [
    'view_dashboard',
    'manage_orders',
    'manage_inventory',
    'view_customers',
    'view_reports',
    'manage_settings',
  ],
};

function App() {
  const [session, setSession] = useState(null);

  const handleAuthenticated = (payload) => {
    if (!payload) {
      return;
    }

    const permissions = Array.isArray(payload.permissions) ? payload.permissions : [];
    const role = payload.role ?? 'Colaborador';

    setSession({ ...payload, permissions, role });
  };

  const handleQuickLogin = () => {
    handleAuthenticated(QUICK_LOGIN_USER);
  };

  const handleLogout = () => {
    setSession(null);
  };

  if (session) {
    return <MainLayout user={session} onLogout={handleLogout} />;
  }

  return (
    <main>
      <LoginView onAuthenticated={handleAuthenticated} onQuickLogin={handleQuickLogin} />
    </main>
  );
}

export default App;
