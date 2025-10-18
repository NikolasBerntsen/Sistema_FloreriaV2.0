import React, { useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { z } from 'zod';

import {
  CustomerPayload,
  CustomerRecord,
  fetchSummary,
  getCustomer,
  updateCustomer,
  deactivateCustomer,
} from '../api/customers';
import { DashboardLayout } from '../components/DashboardLayout';
import { useNotifications } from '../providers/NotificationProvider';

const schema = z.object({
  firstName: z.string().min(1, 'El nombre es obligatorio'),
  lastName: z.string().optional(),
  email: z.string().email('Ingrese un correo válido'),
  phone: z.string().min(5, 'Ingrese un teléfono válido'),
  taxId: z.string().optional(),
  status: z.enum(['active', 'inactive']),
});

type FormValues = z.infer<typeof schema>;

const CustomerDetailRoute: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const customerId = Number(id);
  const { notify } = useNotifications();
  const queryClient = useQueryClient();
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({
    defaultValues: {
      firstName: '',
      lastName: '',
      email: '',
      phone: '',
      taxId: '',
      status: 'active',
    },
  });

  const { data: customer, isLoading } = useQuery({
    queryKey: ['customer', customerId],
    enabled: !!customerId,
    queryFn: () => getCustomer(customerId),
    onError: () => {
      notify({
        kind: 'error',
        title: 'No se encontró el cliente',
        description: 'Regresando al listado.',
      });
      navigate('/customers');
    },
  });

  const { data: summary } = useQuery({
    queryKey: ['customer-summary', customerId],
    enabled: !!customerId,
    queryFn: () => fetchSummary(customerId),
    staleTime: 30_000,
  });

  useEffect(() => {
    if (customer) {
      reset({
        firstName: customer.firstName,
        lastName: customer.lastName,
        email: customer.email,
        phone: customer.phone,
        taxId: customer.taxId ?? '',
        status: customer.status,
      });
    }
  }, [customer, reset]);

  const updateMutation = useMutation({
    mutationFn: (payload: Partial<CustomerPayload>) => updateCustomer(customerId, payload),
    onSuccess: (updated: CustomerRecord) => {
      queryClient.invalidateQueries({ queryKey: ['customers'] });
      queryClient.setQueryData(['customer', customerId], updated);
      notify({ kind: 'success', title: 'Cambios guardados' });
    },
    onError: (error: any) => {
      notify({
        kind: 'error',
        title: 'No se pudo actualizar',
        description: error.response?.data?.message ?? 'Revise los datos e intente nuevamente.',
      });
    },
  });

  const deactivateMutation = useMutation({
    mutationFn: () => deactivateCustomer(customerId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['customers'] });
      queryClient.invalidateQueries({ queryKey: ['customer', customerId] });
      notify({ kind: 'info', title: 'Cliente desactivado' });
      navigate('/customers');
    },
    onError: (error: any) => {
      notify({
        kind: 'error',
        title: 'No se pudo desactivar',
        description: error.response?.data?.message ?? 'El servidor rechazó la operación.',
      });
    },
  });

  const onSubmit = (values: FormValues) => {
    const parsed = schema.safeParse(values);
    if (!parsed.success) {
      notify({
        kind: 'error',
        title: 'Corrija los errores del formulario',
      });
      return;
    }
    updateMutation.mutate(parsed.data);
  };

  const breadcrumbs = [
    { label: 'Inicio', to: '/' },
    { label: 'Clientes', to: '/customers' },
    { label: customer ? `${customer.firstName} ${customer.lastName}`.trim() || 'Detalle' : 'Detalle' },
  ];

  return (
    <DashboardLayout
      title={customer ? `${customer.firstName} ${customer.lastName}`.trim() || 'Cliente sin nombre' : 'Cliente'}
      subtitle="Edita la información y consulta el resumen financiero"
      breadcrumbs={breadcrumbs}
      actions={
        <button
          type="button"
          onClick={() => deactivateMutation.mutate()}
          disabled={deactivateMutation.isLoading}
          style={{
            background: 'transparent',
            border: '1px solid rgba(0,0,0,0.1)',
            borderRadius: 999,
            padding: '10px 18px',
            cursor: 'pointer',
          }}
        >
          {deactivateMutation.isLoading ? 'Procesando...' : 'Desactivar cliente'}
        </button>
      }
    >
      {isLoading && <p>Cargando información del cliente...</p>}
      {!isLoading && customer && (
        <div style={{ display: 'grid', gap: 24, gridTemplateColumns: '2fr 1fr' }}>
          <form
            onSubmit={handleSubmit(onSubmit)}
            style={{
              background: 'var(--color-surface)',
              padding: 28,
              borderRadius: 16,
              display: 'grid',
              gap: 18,
            }}
          >
            <h3 style={{ margin: 0 }}>Información básica</h3>
            <label style={{ display: 'grid', gap: 6 }}>
              <span>Nombre</span>
              <input
                {...register('firstName', { required: 'Ingrese el nombre' })}
                style={{ padding: '10px 12px', borderRadius: 10, border: '1px solid rgba(0,0,0,0.12)' }}
              />
              {errors.firstName && <span style={{ color: '#c0392b', fontSize: 12 }}>{errors.firstName.message}</span>}
            </label>
            <label style={{ display: 'grid', gap: 6 }}>
              <span>Apellido</span>
              <input
                {...register('lastName')}
                style={{ padding: '10px 12px', borderRadius: 10, border: '1px solid rgba(0,0,0,0.12)' }}
              />
            </label>
            <label style={{ display: 'grid', gap: 6 }}>
              <span>Correo electrónico</span>
              <input
                {...register('email', { required: 'Ingrese un correo válido' })}
                style={{ padding: '10px 12px', borderRadius: 10, border: '1px solid rgba(0,0,0,0.12)' }}
              />
              {errors.email && <span style={{ color: '#c0392b', fontSize: 12 }}>{errors.email.message}</span>}
            </label>
            <label style={{ display: 'grid', gap: 6 }}>
              <span>Teléfono</span>
              <input
                {...register('phone', { required: 'Ingrese un número de contacto' })}
                style={{ padding: '10px 12px', borderRadius: 10, border: '1px solid rgba(0,0,0,0.12)' }}
              />
              {errors.phone && <span style={{ color: '#c0392b', fontSize: 12 }}>{errors.phone.message}</span>}
            </label>
            <label style={{ display: 'grid', gap: 6 }}>
              <span>Identificación</span>
              <input
                {...register('taxId')}
                style={{ padding: '10px 12px', borderRadius: 10, border: '1px solid rgba(0,0,0,0.12)' }}
              />
            </label>
            <label style={{ display: 'grid', gap: 6 }}>
              <span>Estado</span>
              <select
                {...register('status')}
                style={{ padding: '10px 12px', borderRadius: 10, border: '1px solid rgba(0,0,0,0.12)' }}
              >
                <option value="active">Activo</option>
                <option value="inactive">Inactivo</option>
              </select>
            </label>
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 12 }}>
              <button
                type="submit"
                disabled={isSubmitting || updateMutation.isLoading}
                style={{
                  background: 'var(--color-primary)',
                  color: 'white',
                  border: 'none',
                  borderRadius: 12,
                  padding: '12px 24px',
                  fontWeight: 600,
                  cursor: 'pointer',
                }}
              >
                {updateMutation.isLoading ? 'Guardando...' : 'Guardar cambios'}
              </button>
            </div>
          </form>

          <section
            style={{
              background: 'var(--color-surface)',
              padding: 28,
              borderRadius: 16,
              display: 'grid',
              gap: 16,
              height: 'fit-content',
            }}
          >
            <h3 style={{ margin: 0 }}>Resumen financiero</h3>
            {summary ? (
              <dl style={{ display: 'grid', gap: 12 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <dt>Pedidos registrados</dt>
                  <dd>{summary.orders.count}</dd>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <dt>Monto total de pedidos</dt>
                  <dd>{formatCurrency(summary.orders.totalAmount)}</dd>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <dt>Saldo pendiente (pedidos)</dt>
                  <dd>{formatCurrency(summary.orders.balanceDue)}</dd>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <dt>Pagos registrados</dt>
                  <dd>{summary.payments.count}</dd>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <dt>Monto total pagado</dt>
                  <dd>{formatCurrency(summary.payments.totalPaid)}</dd>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <dt>Saldo por cobrar</dt>
                  <dd>{formatCurrency(summary.outstandingBalance)}</dd>
                </div>
              </dl>
            ) : (
              <p>No hay datos financieros disponibles.</p>
            )}
          </section>
        </div>
      )}
    </DashboardLayout>
  );
};

const formatCurrency = (value: number) =>
  new Intl.NumberFormat('es-MX', { style: 'currency', currency: 'MXN' }).format(value ?? 0);

export default CustomerDetailRoute;
