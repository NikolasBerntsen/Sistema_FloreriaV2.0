import React from 'react';
import { useForm } from 'react-hook-form';
import { useNavigate } from 'react-router-dom';

import { useAuth } from '../providers/AuthProvider';

interface LoginForm {
  email: string;
  password: string;
}

const LoginRoute: React.FC = () => {
  const { register, handleSubmit, formState } = useForm<LoginForm>({
    defaultValues: { email: '', password: '' },
  });
  const navigate = useNavigate();
  const { login, loading } = useAuth();

  const onSubmit = async (values: LoginForm) => {
    try {
      await login(values.email, values.password);
      navigate('/');
    } catch (error) {
      // El proveedor de autenticación ya notifica el error.
    }
  };

  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: '1fr 1fr',
        minHeight: '100vh',
        background: 'var(--color-background)',
      }}
    >
      <section
        style={{
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          padding: '0 80px',
          background: 'var(--color-surface)',
        }}
      >
        <h1 style={{ fontSize: 32, marginBottom: 8 }}>Florería Carlitos</h1>
        <p style={{ color: 'var(--color-text-muted)' }}>
          Gestiona clientes, pedidos y pagos desde una interfaz moderna.
        </p>
        <form onSubmit={handleSubmit(onSubmit)} style={{ marginTop: 36, display: 'grid', gap: 18 }}>
          <label style={{ display: 'grid', gap: 6 }}>
            <span>Correo electrónico</span>
            <input
              type="email"
              {...register('email', { required: 'El correo es obligatorio' })}
              placeholder="usuario@floreria.com"
              style={{
                padding: '12px 14px',
                borderRadius: 10,
                border: '1px solid rgba(0,0,0,0.1)',
              }}
            />
            {formState.errors.email && (
              <span style={{ color: '#e74c3c', fontSize: 12 }}>{formState.errors.email.message}</span>
            )}
          </label>
          <label style={{ display: 'grid', gap: 6 }}>
            <span>Contraseña</span>
            <input
              type="password"
              {...register('password', { required: 'La contraseña es obligatoria' })}
              placeholder="••••••••"
              style={{
                padding: '12px 14px',
                borderRadius: 10,
                border: '1px solid rgba(0,0,0,0.1)',
              }}
            />
            {formState.errors.password && (
              <span style={{ color: '#e74c3c', fontSize: 12 }}>{formState.errors.password.message}</span>
            )}
          </label>
          <button
            type="submit"
            disabled={loading}
            style={{
              background: 'var(--color-primary)',
              color: 'white',
              border: 'none',
              borderRadius: 12,
              padding: '12px 18px',
              fontWeight: 600,
              cursor: 'pointer',
            }}
          >
            {loading ? 'Verificando...' : 'Iniciar sesión'}
          </button>
        </form>
        <p style={{ marginTop: 24, fontSize: 12, color: 'var(--color-text-muted)' }}>
          Al iniciar sesión aceptas las políticas de uso interno.
        </p>
      </section>
      <section
        style={{
          background: 'linear-gradient(160deg, rgba(200,92,92,0.85), rgba(241,196,15,0.8)), url(https://images.unsplash.com/photo-1524592094714-0f0654e20314?auto=format&fit=crop&w=1000&q=80)',
          backgroundSize: 'cover',
          backgroundPosition: 'center',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'white',
          padding: 40,
          textAlign: 'center',
        }}
      >
        <div style={{ maxWidth: 360 }}>
          <h2 style={{ fontSize: 26 }}>Bienvenido de nuevo</h2>
          <p>
            Toda la operación diaria de la florería en un solo lugar: clientes,
            pedidos, pagos y reportes a un clic de distancia.
          </p>
        </div>
      </section>
    </div>
  );
};

export default LoginRoute;
