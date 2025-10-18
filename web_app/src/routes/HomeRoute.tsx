import React from 'react';

import { DashboardLayout } from '../components/DashboardLayout';

const HomeRoute: React.FC = () => {
  return (
    <DashboardLayout title="Inicio" subtitle="Resumen rápido de la operación diaria">
      <section
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
          gap: 24,
        }}
      >
        <article
          style={{
            background: 'var(--color-surface)',
            borderRadius: 16,
            padding: 24,
            boxShadow: '0 12px 24px rgba(0,0,0,0.08)',
          }}
        >
          <h3 style={{ marginTop: 0 }}>Clientes activos</h3>
          <p style={{ fontSize: 32, margin: '12px 0', fontWeight: 600 }}>--</p>
          <p style={{ margin: 0, color: 'var(--color-text-muted)' }}>
            Este módulo mostrará indicadores clave una vez que la API los exponga.
          </p>
        </article>
        <article
          style={{
            background: 'var(--color-surface)',
            borderRadius: 16,
            padding: 24,
            boxShadow: '0 12px 24px rgba(0,0,0,0.08)',
          }}
        >
          <h3 style={{ marginTop: 0 }}>Pedidos del día</h3>
          <p style={{ fontSize: 32, margin: '12px 0', fontWeight: 600 }}>--</p>
          <p style={{ margin: 0, color: 'var(--color-text-muted)' }}>
            Integrar con el backend permitirá completar este panel.
          </p>
        </article>
      </section>
    </DashboardLayout>
  );
};

export default HomeRoute;
