# Inventario de pantallas de la aplicación de escritorio legada

Este documento resume la navegación, formularios y acciones disponibles en la
interfaz Tkinter actual. La información se recopiló a partir de los módulos
`desktop_app/main.py`, `desktop_app/app/ui/main_window.py`,
`desktop_app/app/ui/admin/setup_dialog.py` y `desktop_app/app/ui/customers/`.

## Flujo de autenticación
- **Pantalla de inicio de sesión** (`FloreriaApp._build_login_view`): formulario con
  campos de correo y contraseña, botón para iniciar sesión y mensajes de error en
  la barra de estado inferior. Utiliza la marca personalizada y puede mostrar un
  eslogan si está configurado. 【F:desktop_app/main.py†L54-L137】【F:desktop_app/main.py†L167-L205】
- **Validación de credenciales**: invoca `authenticate` y muestra cuadros de
  diálogo (`messagebox.showerror/showinfo`). Si la autenticación falla por
  permisos, se notifica mediante la barra de estado. 【F:desktop_app/main.py†L264-L337】
- **Gestión de sesión**: mantiene información del usuario activo en la barra de
  estado y permite cerrar sesión desde el menú principal. 【F:desktop_app/main.py†L339-L410】

## Configuración inicial de administrador
- **Diálogo modal** (`InitialAdminDialog`): ventana emergente que guía la creación
  del primer usuario administrador cuando la base está vacía. Incluye campos de
  nombre, apellido, correo, contraseña y confirmación, con validaciones básicas.
  Muestra mensajes de estado en la propia ventana y utiliza `messagebox` para
  notificar éxito o errores inesperados. 【F:desktop_app/app/ui/admin/setup_dialog.py†L23-L158】

## Ventana principal
- **Layout general** (`MainWindow`): cabecera con logotipo, nombre comercial y
  breadcrumbs; botones de navegación (atrás, inicio, adelante) con atajos de
  teclado. Cuerpo dividido en menú lateral y área de contenido. 【F:desktop_app/app/ui/main_window.py†L1-L167】
- **Menú lateral**: configurable mediante `MenuItem`, aplica estilos primario y
  secundario e incorpora tooltips y atajos personalizados. 【F:desktop_app/app/ui/main_window.py†L22-L125】
- **Gestión de navegación**: controlador interno que actualiza breadcrumbs y
  habilita/deshabilita botones según el historial. 【F:desktop_app/app/ui/main_window.py†L126-L221】

## Gestión de clientes
### Listado (`CustomerListView`)
- **Filtros**: búsqueda por texto, filtro por estado (activo/inactivo/todos),
  botones para aplicar y limpiar filtros. 【F:desktop_app/app/ui/customers/list_view.py†L33-L90】
- **Acciones masivas**: exportación a CSV, importación en modo vista previa o
  commit, creación de nuevo cliente. 【F:desktop_app/app/ui/customers/list_view.py†L60-L92】
- **Tabla de resultados**: muestra nombre, correo, teléfono y estado con
  paginación (`Página X de Y`). Selección simple con doble clic para abrir el
  detalle. 【F:desktop_app/app/ui/customers/list_view.py†L94-L191】
- **Carga de datos**: utiliza `customer_service.list_customers` con paginación y
  ordenamiento, manteniendo el estado actual y habilitando navegación entre
  páginas. 【F:desktop_app/app/ui/customers/list_view.py†L193-L255】

### Detalle (`CustomerDetailView`)
- **Formulario editable**: campos de nombres, contacto, identificación y estado
  con lista desplegable. Botones para guardar cambios y desactivar al cliente.
  Valida datos antes de enviar y muestra notificaciones con `messagebox`.
  【F:desktop_app/app/ui/customers/detail_view.py†L15-L112】【F:desktop_app/app/ui/customers/detail_view.py†L121-L170】
- **Resumen financiero**: indicadores de pedidos y pagos (conteo, montos y
  saldos) con botón para refrescar la información. 【F:desktop_app/app/ui/customers/detail_view.py†L71-L119】

## Flujos adicionales
- **Carga inicial de datos**: tras autenticar, `FloreriaApp` configura la ventana
  principal, registra vistas (Inicio, Clientes, etc.) y controla la navegación al
  detalle de clientes seleccionado. 【F:desktop_app/main.py†L207-L327】【F:desktop_app/main.py†L352-L410】
- **Bitácora/Auditoría**: registra eventos de login/logout y navegación mediante
  `log_audit`. 【F:desktop_app/main.py†L284-L307】【F:desktop_app/main.py†L384-L410】

Este inventario servirá como referencia para alcanzar paridad funcional en la
nueva interfaz web/electrónica.
