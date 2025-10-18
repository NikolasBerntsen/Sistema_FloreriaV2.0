import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { z } from 'zod';

import { createCustomer, CustomerPayload } from '../api/customers';
import { DashboardLayout } from '../components/DashboardLayout';
import { useNotifications } from '../providers/NotificationProvider';

const schema = z.object({
  firstName: z.string().min(1, 'Ingrese el nombre'),
  lastName: z.string().optional(),
  email: z.string().email('Correo inválido'),
  phone: z.string().min(5, 'Teléfono inválido'),
  taxId: z.string().optional(),
  status: z.enum(['active', 'inactive']).default('active'),
});

type FormValues = z.infer<typeof schema>;

const CustomerCreateRoute: React.FC = () => {
  const navigate = useNavigate();
  const { notify } = useNotifications();
  const queryClient = useQueryClient();
  const {
    register,
    handleSubmit,
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

  const mutation = useMutation({
    mutationFn: (payload: CustomerPayload) => createCustomer(payload),
    onSuccess: (customer) => {
      queryClient.invalidateQueries({ queryKey: ['customers'] });
      notify({ kind: 'success', title: 'Cliente creado', description: 'Ahora puedes completar su información.' });
      navigate(`/customers/${customer.id}`);
    },
    onError: (error: any) => {
      notify({
        kind: 'error',
        title: 'No se pudo crear el cliente',
        description: error.response?.data?.message ?? 'Verifica los datos e intenta nuevamente.',
      });
    },
  });

  const onSubmit = (values: FormValues) => {
    const parsed = schema.safeParse(values);
    if (!parsed.success) {
      notify({ kind: 'error', title: 'Corrige los errores del formulario' });
      return;
    }
    mutation.mutate(parsed.data as CustomerPayload);
  };

  return (
    <DashboardLayout
      title="Nuevo cliente"
      subtitle="Registra un nuevo cliente en el directorio"
      breadcrumbs={[{ label: 'Inicio', to: '/' }, { label: 'Clientes', to: '/customers' }, { label: 'Nuevo' }]}
    >
      <form
        onSubmit={handleSubmit(onSubmit)}
        style={{
          background: 'var(--color-surface)',
          padding: 32,
          borderRadius: 18,
          maxWidth: 720,
          display: 'grid',
          gap: 18,
        }}
      >
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
            {...register('email', { required: 'Ingrese un correo' })}
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
            type="button"
            onClick={() => navigate(-1)}
            style={{
              background: 'transparent',
              border: '1px solid rgba(0,0,0,0.12)',
              borderRadius: 12,
              padding: '12px 20px',
              cursor: 'pointer',
            }}
          >
            Cancelar
          </button>
          <button
            type="submit"
            disabled={isSubmitting || mutation.isLoading}
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
            {mutation.isLoading ? 'Creando...' : 'Guardar cliente'}
          </button>
        </div>
      </form>
    </DashboardLayout>
  );
};

export default CustomerCreateRoute;
