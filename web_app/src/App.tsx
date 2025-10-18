import React from 'react';
import { Navigate, Route, Routes } from 'react-router-dom';

import { useAuth } from './providers/AuthProvider';
import LoginRoute from './routes/LoginRoute';
import HomeRoute from './routes/HomeRoute';
import CustomersListRoute from './routes/CustomersListRoute';
import CustomerDetailRoute from './routes/CustomerDetailRoute';
import CustomerUtilitiesRoute from './routes/CustomerUtilitiesRoute';
import CustomerCreateRoute from './routes/CustomerCreateRoute';

const PrivateRoute: React.FC<React.PropsWithChildren> = ({ children }) => {
  const { user, loading } = useAuth();
  if (loading) {
    return (
      <div style={{ display: 'grid', placeItems: 'center', height: '100vh' }}>
        <p>Cargando sesión...</p>
      </div>
    );
  }
  if (!user) {
    return <Navigate to="/login" replace />;
  }
  return <>{children}</>;
};

const App: React.FC = () => {
  return (
    <Routes>
      <Route path="/login" element={<LoginRoute />} />
      <Route
        path="/"
        element={
          <PrivateRoute>
            <HomeRoute />
          </PrivateRoute>
        }
      />
      <Route
        path="/customers"
        element={
          <PrivateRoute>
            <CustomersListRoute />
          </PrivateRoute>
        }
      />
      <Route
        path="/customers/new"
        element={
          <PrivateRoute>
            <CustomerCreateRoute />
          </PrivateRoute>
        }
      />
      <Route
        path="/customers/:id"
        element={
          <PrivateRoute>
            <CustomerDetailRoute />
          </PrivateRoute>
        }
      />
      <Route
        path="/customers/utilities"
        element={
          <PrivateRoute>
            <CustomerUtilitiesRoute />
          </PrivateRoute>
        }
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
};

export default App;
