import React, { useState } from 'react';
import { useMutation } from '@tanstack/react-query';

import {
  exportCustomersCsv,
  importCustomersCsv,
  CustomerListParams,
} from '../api/customers';
import { DashboardLayout } from '../components/DashboardLayout';
import { useNotifications } from '../providers/NotificationProvider';
import { buildCsvFileName, downloadBlob } from '../utils/csv';

const CustomerUtilitiesRoute: React.FC = () => {
  const { notify } = useNotifications();
  const [file, setFile] = useState<File | null>(null);
  const [statusFilter, setStatusFilter] = useState<CustomerListParams['status']>('all');

  const exportMutation = useMutation({
    mutationFn: (params: CustomerListParams) => exportCustomersCsv(params),
    onSuccess: (blob) => {
      downloadBlob(blob, buildCsvFileName('clientes'));
      notify({ kind: 'success', title: 'Exportación generada', description: 'La descarga comenzará enseguida.' });
    },
    onError: () => {
      notify({ kind: 'error', title: 'No se pudo exportar', description: 'Intente nuevamente más tarde.' });
    },
  });

  const importMutation = useMutation({
    mutationFn: (mode: 'preview' | 'commit') => {
      if (!file) {
        throw new Error('Seleccione un archivo CSV primero');
      }
      return importCustomersCsv(file, mode);
    },
    onSuccess: (result, mode) => {
      notify({
        kind: mode === 'commit' ? 'success' : 'info',
        title: mode === 'commit' ? 'Importación completada' : 'Vista previa generada',
        description:
          mode === 'commit'
            ? `${result.imported} registros importados correctamente. ${result.errors.length} errores.`
            : `${result.rows} filas analizadas. ${result.errors.length} incidencias detectadas.`,
      });
    },
    onError: (error: any) => {
      notify({
        kind: 'error',
        title: 'La importación falló',
        description: error.message ?? 'El servidor rechazó el archivo proporcionado.',
      });
    },
  });

  return (
    <DashboardLayout
      title="Utilidades CSV"
      subtitle="Sincroniza clientes mediante exportaciones e importaciones controladas"
      breadcrumbs={[{ label: 'Inicio', to: '/' }, { label: 'Clientes', to: '/customers' }, { label: 'Utilidades CSV' }]}
    >
      <section
        style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: 24,
        }}
      >
        <article
          style={{
            background: 'var(--color-surface)',
            borderRadius: 16,
            padding: 28,
            display: 'grid',
            gap: 16,
          }}
        >
          <h3 style={{ margin: 0 }}>Exportar directorio</h3>
          <p style={{ margin: 0, color: 'var(--color-text-muted)' }}>
            Descarga un archivo CSV con los clientes filtrados por estado. Compatible con Excel,
            Google Sheets y otras herramientas.
          </p>
          <label style={{ display: 'grid', gap: 6 }}>
            <span>Estado</span>
            <select
              value={statusFilter ?? 'all'}
              onChange={(event) => setStatusFilter(event.target.value as typeof statusFilter)}
              style={{ padding: '10px 12px', borderRadius: 12, border: '1px solid rgba(0,0,0,0.12)' }}
            >
              <option value="all">Todos</option>
              <option value="active">Solo activos</option>
              <option value="inactive">Solo inactivos</option>
            </select>
          </label>
          <button
            type="button"
            onClick={() => exportMutation.mutate({ status: statusFilter })}
            disabled={exportMutation.isLoading}
            style={{
              background: 'var(--color-primary)',
              color: 'white',
              border: 'none',
              borderRadius: 12,
              padding: '12px 20px',
              fontWeight: 600,
              cursor: 'pointer',
            }}
          >
            {exportMutation.isLoading ? 'Generando...' : 'Descargar CSV'}
          </button>
        </article>

        <article
          style={{
            background: 'var(--color-surface)',
            borderRadius: 16,
            padding: 28,
            display: 'grid',
            gap: 16,
          }}
        >
          <h3 style={{ margin: 0 }}>Importar desde CSV</h3>
          <p style={{ margin: 0, color: 'var(--color-text-muted)' }}>
            Asegúrate de usar el formato de plantilla oficial. Primero genera una vista previa para
            revisar los posibles errores.
          </p>
          <input
            type="file"
            accept=".csv"
            onChange={(event) => setFile(event.target.files?.[0] ?? null)}
          />
          <div style={{ display: 'flex', gap: 12 }}>
            <button
              type="button"
              onClick={() => importMutation.mutate('preview')}
              disabled={importMutation.isLoading}
              style={{
                background: 'transparent',
                border: '1px solid rgba(0,0,0,0.1)',
                borderRadius: 12,
                padding: '12px 20px',
                cursor: 'pointer',
              }}
            >
              Vista previa
            </button>
            <button
              type="button"
              onClick={() => importMutation.mutate('commit')}
              disabled={importMutation.isLoading}
              style={{
                background: 'var(--color-primary)',
                color: 'white',
                border: 'none',
                borderRadius: 12,
                padding: '12px 20px',
                fontWeight: 600,
                cursor: 'pointer',
              }}
            >
              Aplicar cambios
            </button>
          </div>
          {importMutation.isLoading && <p>Procesando archivo...</p>}
        </article>
      </section>
    </DashboardLayout>
  );
};

export default CustomerUtilitiesRoute;
