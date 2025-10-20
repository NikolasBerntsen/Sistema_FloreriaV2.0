import { useState } from 'react';
import PropTypes from 'prop-types';
import styles from './LoginView.module.css';
import { login } from '../../services/authService';
import { colors, typography } from '../../design/tokens';

const EMAIL_REGEX = /^[\w.+-]+@([\w-]+\.)+[\w-]{2,}$/u;

const initialFormState = {
  username: '',
  password: '',
};

function validate(formState) {
  const newErrors = {};

  if (!formState.username.trim()) {
    newErrors.username = 'Ingresa tu correo electrónico corporativo.';
  } else if (!EMAIL_REGEX.test(formState.username.trim())) {
    newErrors.username = 'El correo electrónico no tiene un formato válido.';
  }

  if (!formState.password) {
    newErrors.password = 'Ingresa tu contraseña de acceso.';
  } else if (formState.password.length < 6) {
    newErrors.password = 'La contraseña debe tener al menos 6 caracteres.';
  }

  return newErrors;
}

function LoginView({ onAuthenticated, onQuickLogin }) {
  const [formState, setFormState] = useState(initialFormState);
  const [errors, setErrors] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [status, setStatus] = useState(null);

  const handleChange = (event) => {
    const { name, value } = event.target;
    setFormState((prev) => ({ ...prev, [name]: value }));
    setErrors((prev) => ({ ...prev, [name]: undefined }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setStatus(null);

    const validationErrors = validate(formState);
    setErrors(validationErrors);

    if (Object.keys(validationErrors).length > 0) {
      return;
    }

    try {
      setIsSubmitting(true);
      const response = await login(formState);
      setStatus({
        type: 'success',
        message: `Bienvenido ${response.full_name}, tu sesión está lista.`,
      });
      setFormState(initialFormState);
      if (typeof onAuthenticated === 'function') {
        onAuthenticated(response);
      }
    } catch (error) {
      setStatus({
        type: 'error',
        message: error.message ?? 'No fue posible iniciar sesión en este momento.',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleQuickLoginClick = () => {
    if (typeof onQuickLogin === 'function') {
      onQuickLogin();
    }
  };

  const statusClassName = status
    ? [
        styles.statusMessage,
        status.type === 'success' ? styles.statusSuccess : styles.statusError,
      ].join(' ')
    : undefined;

  return (
    <div className={styles.container}>
      <div className={styles.logo}>
        <div className={styles.logoBadge}>FC</div>
        <div className={styles.logoText}>
          <h1 className={styles.title}>Florería Carlitos</h1>
          <p className={styles.subtitle}>Panel administrativo</p>
        </div>
      </div>

      <form className={styles.card} onSubmit={handleSubmit} noValidate>
        <header>
          <h2 style={{ margin: 0, fontSize: typography.headingSm }}>Inicia sesión</h2>
          <p style={{ margin: '8px 0 0', color: colors.neutral600 }}>
            Usa tus credenciales asignadas por el supervisor.
          </p>
        </header>

        <div className={styles.field}>
          <label htmlFor="username">Correo electrónico</label>
          <div className={styles.inputWrapper}>
            <input
              id="username"
              name="username"
              type="email"
              autoComplete="username"
              placeholder="tucorreo@floreriacarlitos.com"
              value={formState.username}
              onChange={handleChange}
              aria-invalid={Boolean(errors.username)}
              aria-describedby={errors.username ? 'username-error' : undefined}
              disabled={isSubmitting}
            />
          </div>
          {errors.username ? (
            <span id="username-error" className={styles.errorText}>
              {errors.username}
            </span>
          ) : (
            <span className={styles.helper}>Debes utilizar tu correo institucional.</span>
          )}
        </div>

        <div className={styles.field}>
          <label htmlFor="password">Contraseña</label>
          <div className={styles.inputWrapper}>
            <input
              id="password"
              name="password"
              type="password"
              autoComplete="current-password"
              placeholder="••••••"
              value={formState.password}
              onChange={handleChange}
              aria-invalid={Boolean(errors.password)}
              aria-describedby={errors.password ? 'password-error' : undefined}
              disabled={isSubmitting}
            />
          </div>
          {errors.password ? (
            <span id="password-error" className={styles.errorText}>
              {errors.password}
            </span>
          ) : (
            <span className={styles.helper}>Mínimo 6 caracteres, distingue mayúsculas.</span>
          )}
        </div>

        {status ? (
          <div className={statusClassName} role={status.type === 'error' ? 'alert' : 'status'}>
            {status.message}
          </div>
        ) : null}

        <div className={styles.actions}>
          <button className={styles.buttonPrimary} type="submit" disabled={isSubmitting}>
            {isSubmitting ? 'Verificando…' : 'Ingresar'}
          </button>
          <button
            className={styles.buttonDev}
            type="button"
            onClick={handleQuickLoginClick}
            disabled={isSubmitting}
          >
            Acceso rápido para desarrollo
          </button>
        </div>

        <p className={styles.secondaryAction}>
          ¿Olvidaste tu contraseña?{' '}
          <a href="mailto:soporte@floreriacarlitos.com">Contacta soporte</a>
        </p>
      </form>
    </div>
  );
}

LoginView.propTypes = {
  onAuthenticated: PropTypes.func,
  onQuickLogin: PropTypes.func,
};

LoginView.defaultProps = {
  onAuthenticated: undefined,
  onQuickLogin: undefined,
};

export default LoginView;
