import { useCallback, useEffect, useMemo, useRef, useState } from 'react';

const MENU_ITEMS = [
  {
    id: 'dashboard',
    label: 'Panel principal',
    description: 'Visión general del negocio y métricas clave.',
    requiredPermission: 'view_dashboard',
    placeholder: {
      title: 'Panel principal en construcción',
      description:
        'Aquí podrás consultar indicadores clave, ventas recientes y otra información relevante.',
    },
  },
  {
    id: 'orders',
    label: 'Pedidos',
    description: 'Gestiona pedidos y su estado de entrega.',
    requiredPermission: 'manage_orders',
    placeholder: {
      title: 'Gestión de pedidos próximamente',
      description: 'Podrás crear, editar y monitorear pedidos a medida que integremos el backend.',
    },
  },
  {
    id: 'inventory',
    label: 'Inventario',
    description: 'Control de productos y existencias.',
    requiredPermission: 'manage_inventory',
    placeholder: {
      title: 'Inventario en preparación',
      description:
        'Se mostrará la disponibilidad de arreglos y materias primas, con alertas automáticas.',
    },
  },
  {
    id: 'customers',
    label: 'Clientes',
    description: 'Directorio y seguimiento de clientes frecuentes.',
    requiredPermission: 'view_customers',
    placeholder: {
      title: 'Módulo de clientes en camino',
      description:
        'Mantendrás un historial de clientes, preferencias y recordatorios de fechas especiales.',
    },
  },
  {
    id: 'reports',
    label: 'Reportes',
    description: 'Reportes de ventas, rendimiento y métricas.',
    requiredPermission: 'view_reports',
    placeholder: {
      title: 'Reportes automáticos muy pronto',
      description: 'Podrás descargar informes en PDF y Excel para compartir con la gerencia.',
    },
  },
  {
    id: 'settings',
    label: 'Configuración',
    description: 'Preferencias y administración del sistema.',
    requiredPermission: 'manage_settings',
    placeholder: {
      title: 'Configuración centralizada',
      description: 'Desde aquí ajustarás permisos, catálogos y personalizaciones del sistema.',
    },
  },
];

export function useMainNavigation(userPermissions = []) {
  const normalizedPermissions = useMemo(
    () => new Set(Array.isArray(userPermissions) ? userPermissions : []),
    [userPermissions],
  );

  const [activeRoute, setActiveRoute] = useState(() => {
    const firstAllowed = MENU_ITEMS.find(
      (item) => !item.requiredPermission || normalizedPermissions.has(item.requiredPermission),
    );
    return firstAllowed?.id ?? MENU_ITEMS[0].id;
  });

  const contentRegistry = useRef(new Map());
  const [, forceRender] = useState(0);

  const menuItems = useMemo(
    () =>
      MENU_ITEMS.map((item) => ({
        ...item,
        isAllowed: !item.requiredPermission || normalizedPermissions.has(item.requiredPermission),
      })),
    [normalizedPermissions],
  );

  const allowedRouteIds = useMemo(
    () => menuItems.filter((item) => item.isAllowed).map((item) => item.id),
    [menuItems],
  );

  useEffect(() => {
    if (allowedRouteIds.length === 0) {
      setActiveRoute(MENU_ITEMS[0].id);
      return;
    }

    if (!allowedRouteIds.includes(activeRoute)) {
      setActiveRoute(allowedRouteIds[0]);
    }
  }, [activeRoute, allowedRouteIds]);

  const selectRoute = useCallback(
    (routeId) => {
      const target = menuItems.find((item) => item.id === routeId);
      if (!target || !target.isAllowed) {
        return;
      }
      setActiveRoute(routeId);
    },
    [menuItems],
  );

  const activeItem = useMemo(
    () => menuItems.find((item) => item.id === activeRoute) ?? menuItems[0],
    [activeRoute, menuItems],
  );

  const registerContentHook = useCallback((routeId, renderer) => {
    if (!routeId || typeof renderer !== 'function') {
      return () => {};
    }

    contentRegistry.current.set(routeId, renderer);
    forceRender((value) => value + 1);

    return () => {
      contentRegistry.current.delete(routeId);
      forceRender((value) => value + 1);
    };
  }, []);

  const activeContentRenderer = activeItem ? contentRegistry.current.get(activeItem.id) : undefined;

  return {
    menuItems,
    activeItem,
    selectRoute,
    activeContentRenderer,
    placeholderContent: activeItem?.placeholder,
    registerContentHook,
  };
}
