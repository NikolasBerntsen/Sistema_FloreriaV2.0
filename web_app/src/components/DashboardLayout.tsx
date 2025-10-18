import React from 'react';
import { Link, NavLink, useNavigate } from 'react-router-dom';
import clsx from 'clsx';

import { useAuth } from '../providers/AuthProvider';

export interface BreadcrumbItem {
  label: string;
  to?: string;
}

export interface DashboardLayoutProps {
  title: string;
  subtitle?: string;
  breadcrumbs?: BreadcrumbItem[];
  actions?: React.ReactNode;
  children: React.ReactNode;
}

const menuItems = [
  { label: 'Inicio', to: '/' },
  { label: 'Clientes', to: '/customers' },
  { label: 'Utilidades CSV', to: '/customers/utilities' },
];

export const DashboardLayout: React.FC<DashboardLayoutProps> = ({
  title,
  subtitle,
  breadcrumbs = [],
  actions,
  children,
}) => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  return (
    <div style={{ display: 'flex', minHeight: '100vh' }}>
      <aside
        style={{
          width: 240,
          background: 'var(--color-surface)',
          borderRight: '1px solid rgba(0,0,0,0.08)',
          padding: '32px 24px',
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        <Link to="/" style={{ textDecoration: 'none', color: 'var(--color-primary)' }}>
          <h1 style={{ margin: 0, fontSize: 22 }}>Florería Carlitos</h1>
        </Link>
        <p style={{ color: 'var(--color-text-muted)', marginTop: 4 }}>Panel de operaciones</p>
        <nav style={{ marginTop: 32, display: 'flex', flexDirection: 'column', gap: 8 }}>
          {menuItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                clsx('menu-link', isActive && 'menu-link--active')
              }
              style={({ isActive }) => ({
                padding: '10px 14px',
                borderRadius: 10,
                textDecoration: 'none',
                color: isActive ? 'var(--color-surface)' : 'var(--color-text)',
                background: isActive ? 'var(--color-primary)' : 'transparent',
                fontWeight: isActive ? 600 : 500,
              })}
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div style={{ marginTop: 'auto', fontSize: 12, color: 'var(--color-text-muted)' }}>
          v{__APP_VERSION__}
        </div>
      </aside>
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        <header
          style={{
            background: 'var(--color-surface)',
            borderBottom: '1px solid rgba(0,0,0,0.08)',
            padding: '20px 32px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: 24,
          }}
        >
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              {breadcrumbs.length > 0 && (
                <nav style={{ fontSize: 13, color: 'var(--color-text-muted)' }}>
                  {breadcrumbs.map((crumb, index) => (
                    <React.Fragment key={`${crumb.label}-${index}`}>
                      {index > 0 && <span style={{ margin: '0 8px' }}>›</span>}
                      {crumb.to ? <Link to={crumb.to}>{crumb.label}</Link> : crumb.label}
                    </React.Fragment>
                  ))}
                </nav>
              )}
            </div>
            <h2 style={{ marginBottom: 4 }}>{title}</h2>
            {subtitle && <p style={{ margin: 0, color: 'var(--color-text-muted)' }}>{subtitle}</p>}
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
            {actions}
            {user && (
              <div style={{ textAlign: 'right' }}>
                <div style={{ fontWeight: 600 }}>{`${user.firstName} ${user.lastName}`}</div>
                <div style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>{user.email}</div>
              </div>
            )}
            <button
              type="button"
              onClick={handleLogout}
              style={{
                background: 'var(--color-primary)',
                border: 'none',
                borderRadius: 999,
                color: 'white',
                padding: '10px 18px',
                fontWeight: 600,
                cursor: 'pointer',
              }}
            >
              Cerrar sesión
            </button>
          </div>
        </header>
        <main style={{ padding: '32px', flex: 1 }}>{children}</main>
      </div>
    </div>
  );
};
