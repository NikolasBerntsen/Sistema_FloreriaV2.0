import React, { createContext, useCallback, useContext, useMemo, useState } from 'react';
import { createPortal } from 'react-dom';

export type NotificationKind = 'success' | 'error' | 'info';

export interface NotificationPayload {
  id?: string;
  title: string;
  description?: string;
  kind?: NotificationKind;
  timeout?: number;
}

interface NotificationContextShape {
  notify: (payload: NotificationPayload) => void;
}

interface Toast extends Required<Omit<NotificationPayload, 'timeout'>> {
  timeout: number;
}

const NotificationContext = createContext<NotificationContextShape | undefined>(undefined);

const DEFAULT_TIMEOUT = 5000;

const ToastContainer: React.FC<{ toasts: Toast[]; dismiss: (id: string) => void }> = ({
  toasts,
  dismiss,
}) => {
  return createPortal(
    <div className="toast-container">
      {toasts.map((toast) => (
        <div key={toast.id} className={`toast toast--${toast.kind}`}>
          <h4>{toast.title}</h4>
          {toast.description && <p>{toast.description}</p>}
          <button
            type="button"
            onClick={() => dismiss(toast.id)}
            style={{
              marginTop: 8,
              border: 'none',
              background: 'transparent',
              color: 'var(--color-text-muted)',
              cursor: 'pointer',
              textDecoration: 'underline',
              padding: 0,
            }}
          >
            Cerrar
          </button>
        </div>
      ))}
    </div>,
    document.body
  );
};

export const NotificationProvider: React.FC<React.PropsWithChildren> = ({ children }) => {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const dismiss = useCallback((id: string) => {
    setToasts((items) => items.filter((item) => item.id !== id));
  }, []);

  const notify = useCallback((payload: NotificationPayload) => {
    const id = payload.id ?? crypto.randomUUID();
    const toast: Toast = {
      id,
      title: payload.title,
      description: payload.description ?? '',
      kind: payload.kind ?? 'info',
      timeout: payload.timeout ?? DEFAULT_TIMEOUT,
    };
    setToasts((items) => [...items, toast]);
    if (toast.timeout > 0) {
      window.setTimeout(() => dismiss(id), toast.timeout);
    }
  }, [dismiss]);

  const value = useMemo(() => ({ notify }), [notify]);

  return (
    <NotificationContext.Provider value={value}>
      {children}
      <ToastContainer toasts={toasts} dismiss={dismiss} />
    </NotificationContext.Provider>
  );
};

export const useNotifications = () => {
  const ctx = useContext(NotificationContext);
  if (!ctx) {
    throw new Error('useNotifications debe utilizarse dentro de NotificationProvider');
  }
  return ctx;
};
