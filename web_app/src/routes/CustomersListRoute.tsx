import React, { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';

import {
  CustomerRecord,
  CustomerStatus,
  listCustomers,
  CustomerListParams,
} from '../api/customers';
import { DashboardLayout } from '../components/DashboardLayout';
import { useNotifications } from '../providers/NotificationProvider';

interface Filters {
  search: string;
  status: CustomerStatus | 'all';
  page: number;
}

const defaultFilters: Filters = {
  search: '',
  status: 'all',
  page: 1,
};

const CustomersListRoute: React.FC = () => {
  const navigate = useNavigate();
  const { notify } = useNotifications();
  const [filters, setFilters] = useState<Filters>(defaultFilters);

  const queryParams = useMemo<CustomerListParams>(
    () => ({ page: filters.page, size: 20, search: filters.search || undefined, status: filters.status }),
    [filters]
  );

  const { data, isLoading, refetch, isFetching } = useQuery({
    queryKey: ['customers', queryParams],
    queryFn: () => listCustomers(queryParams),
    keepPreviousData: true,
    onError: (error: any) => {
      notify({
        kind: 'error',
        title: 'No se pudo cargar el listado',
        description: error.response?.data?.message ?? 'Intente nuevamente en unos minutos.',
      });
    },
  });

  const rows: CustomerRecord[] = data?.data ?? [];
  const meta = data?.meta ?? { page: 1, totalPages: 1, total: 0, size: 20 };

  const handleSearchChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setFilters((current) => ({ ...current, search: event.target.value, page: 1 }));
  };

  const handleStatusChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    setFilters((current) => ({ ...current, status: event.target.value as Filters['status'], page: 1 }));
  };

  const handlePagination = (direction: -1 | 1) => {
    setFilters((current) => ({ ...current, page: Math.max(1, current.page + direction) }));
  };

  const handleReset = () => {
    setFilters(defaultFilters);
  };

  const actionBar = (
    <div style={{ display: 'flex', gap: 12 }}>
      <button
        type="button"
        onClick={() => navigate('/customers/new')}
        style={{
          background: 'var(--color-primary)',
          color: 'white',
          border: 'none',
          borderRadius: 999,
          padding: '10px 18px',
          fontWeight: 600,
          cursor: 'pointer',
        }}
      >
        Nuevo cliente
      </button>
      <button
        type="button"
        onClick={() => refetch()}
        style={{
          background: 'transparent',
          border: '1px solid rgba(0,0,0,0.1)',
          borderRadius: 999,
          padding: '10px 18px',
          cursor: 'pointer',
        }}
      >
        Actualizar
      </button>
    </div>
  );

  return (
    <DashboardLayout
      title="Clientes"
      subtitle="Administra el directorio de clientes y accede a su información."
      breadcrumbs={[{ label: 'Inicio', to: '/' }, { label: 'Clientes' }]}
      actions={actionBar}
    >
      <section
        style={{
          display: 'flex',
          gap: 12,
          alignItems: 'center',
          marginBottom: 18,
        }}
      >
        <input
          type="search"
          value={filters.search}
          onChange={handleSearchChange}
          placeholder="Buscar por nombre, correo o teléfono"
          style={{ flex: 2, padding: '10px 14px', borderRadius: 12, border: '1px solid rgba(0,0,0,0.12)' }}
        />
        <select
          value={filters.status}
          onChange={handleStatusChange}
          style={{ flex: 1, padding: '10px 14px', borderRadius: 12, border: '1px solid rgba(0,0,0,0.12)' }}
        >
          <option value="all">Todos</option>
          <option value="active">Activos</option>
          <option value="inactive">Inactivos</option>
        </select>
        <button
          type="button"
          onClick={handleReset}
          style={{
            background: 'transparent',
            border: '1px solid rgba(0,0,0,0.1)',
            borderRadius: 12,
            padding: '10px 18px',
            cursor: 'pointer',
          }}
        >
          Limpiar filtros
        </button>
      </section>

      <div style={{ background: 'var(--color-surface)', borderRadius: 16, overflow: 'hidden' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead style={{ background: 'rgba(0,0,0,0.04)' }}>
            <tr>
              <th style={{ textAlign: 'left', padding: '14px 18px' }}>Nombre</th>
              <th style={{ textAlign: 'left', padding: '14px 18px' }}>Correo</th>
              <th style={{ textAlign: 'left', padding: '14px 18px' }}>Teléfono</th>
              <th style={{ textAlign: 'left', padding: '14px 18px' }}>Estado</th>
            </tr>
          </thead>
          <tbody>
            {isLoading && (
              <tr>
                <td colSpan={4} style={{ textAlign: 'center', padding: 32 }}>
                  Cargando clientes...
                </td>
              </tr>
            )}
            {!isLoading && rows.length === 0 && (
              <tr>
                <td colSpan={4} style={{ textAlign: 'center', padding: 32 }}>
                  No se encontraron clientes con los filtros actuales.
                </td>
              </tr>
            )}
            {rows.map((row) => (
              <tr
                key={row.id}
                onClick={() => navigate(`/customers/${row.id}`)}
                style={{
                  cursor: 'pointer',
                  borderTop: '1px solid rgba(0,0,0,0.05)',
                }}
              >
                <td style={{ padding: '14px 18px' }}>{`${row.firstName} ${row.lastName}`.trim() || '(Sin nombre)'}</td>
                <td style={{ padding: '14px 18px' }}>{row.email}</td>
                <td style={{ padding: '14px 18px' }}>{row.phone}</td>
                <td style={{ padding: '14px 18px' }}>
                  <span
                    style={{
                      padding: '4px 10px',
                      borderRadius: 999,
                      background: row.status === 'active' ? 'rgba(46, 204, 113, 0.16)' : 'rgba(231, 76, 60, 0.16)',
                      color: row.status === 'active' ? '#27ae60' : '#c0392b',
                      fontWeight: 600,
                    }}
                  >
                    {row.status === 'active' ? 'Activo' : 'Inactivo'}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <footer
        style={{
          marginTop: 18,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          color: 'var(--color-text-muted)',
        }}
      >
        <span>
          Página {meta.page} de {meta.totalPages} · {meta.total} clientes
          {isFetching && ' (actualizando...)'}
        </span>
        <div style={{ display: 'flex', gap: 12 }}>
          <button
            type="button"
            disabled={meta.page <= 1}
            onClick={() => handlePagination(-1)}
            style={{
              background: 'transparent',
              border: '1px solid rgba(0,0,0,0.1)',
              borderRadius: 999,
              padding: '8px 18px',
              cursor: 'pointer',
              opacity: meta.page <= 1 ? 0.5 : 1,
            }}
          >
            Anterior
          </button>
          <button
            type="button"
            disabled={meta.page >= meta.totalPages}
            onClick={() => handlePagination(1)}
            style={{
              background: 'transparent',
              border: '1px solid rgba(0,0,0,0.1)',
              borderRadius: 999,
              padding: '8px 18px',
              cursor: 'pointer',
              opacity: meta.page >= meta.totalPages ? 0.5 : 1,
            }}
          >
            Siguiente
          </button>
        </div>
      </footer>
    </DashboardLayout>
  );
};

export default CustomersListRoute;
