# Contratos IPC/HTTP para la aplicación de escritorio

Este documento resume las funciones reutilizables existentes en `desktop_app/app` y define los contratos JSON propuestos para integrar la aplicación de escritorio con un backend o proceso coordinador mediante canales IPC o endpoints HTTP.

## 1. Funciones reutilizables detectadas

| Módulo | Función/Clase | Responsabilidad | Uso recomendado |
| --- | --- | --- | --- |
| `app/services/auth_service.py` | `authenticate(email, password, connection=None)` | Valida credenciales, registra auditoría y abre sesión. | Canal de autenticación inicial (`auth.login`). |
| `app/services/auth_service.py` | `logout()` | Cierra la sesión actual y registra auditoría. | Canal de cierre de sesión (`auth.logout`). |
| `app/services/auth_service.py` | `get_current_session()` / `is_authenticated()` | Expone el estado de sesión para componer respuestas. | Bootstrapping de la app y verificación de permisos. |
| `app/services/branding_service.py` | `get_branding(config)` | Obtiene nombre, logotipo y tagline desde configuración/entorno. | Datos iniciales y cabecera del menú principal. |
| `app/services/customer_service.py` | `list_customers(...)` | Devuelve clientes paginados utilizando filtros existentes. | Futuras vistas que consuman listados en el menú principal. |
| `app/services/customer_service.py` | `get_financial_summary(customer_id, ...)` | Consolida datos de pedidos y pagos, reutilizando repositorios. | Datos iniciales cuando se abra el panel de clientes. |
| `app/services/user_service.py` | `create_initial_admin(connection, data)` | Alta del primer usuario administrador con auditoría. | Flujo de instalación/activación inicial. |
| `app/ui/navigation.py` | `NavigationController` | Gestiona navegación y breadcrumbs para la ventana principal. | Serializar menú principal y estado de navegación en IPC. |
| `app/ui/main_window.py` | `MenuItem` | Modelo para acciones del menú lateral. | Base para la estructura `menu.items` del contrato. |

> Nota: Las funciones señaladas encapsulan reglas de negocio (auditoría, normalización y consultas) que deben centralizarse en el backend. Los canales IPC/HTTP propuestos se apoyan en estas funciones para evitar duplicar lógica en la capa de transporte.

## 2. Canales IPC / Endpoints HTTP propuestos

La siguiente tabla resume los canales propuestos. Cada canal puede exponerse como endpoint REST (`POST /api/auth/login`) o como mensaje IPC (`channel: "auth.login"`).

| Identificador | Método sugerido | Propósito | Funciones reutilizadas |
| --- | --- | --- | --- |
| `auth.login` | `POST` | Autenticar usuario y abrir sesión. | `authenticate`, `get_current_session`, `log_audit`. |
| `auth.logout` | `POST` | Cerrar sesión activa. | `logout`. |
| `app.menu` | `GET` | Recuperar opciones del menú principal según rol. | `NavigationController`, `MenuItem`. |
| `app.bootstrap` | `GET` | Entregar datos iniciales (sesión, branding, menús y banderas). | `get_current_session`, `get_branding`, `NavigationController`. |

## 3. Esquemas JSON de los contratos

Las estructuras siguientes utilizan JSON Schema draft 2020-12 para describir las cargas útiles. Las propiedades marcadas como opcionales pueden omitirse si su valor es `null`.

### 3.1 `auth.login`

- **Request** (`application/json`):

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "LoginRequest",
  "type": "object",
  "required": ["email", "password"],
  "properties": {
    "email": { "type": "string", "format": "email", "minLength": 3 },
    "password": { "type": "string", "minLength": 1 }
  },
  "additionalProperties": false
}
```

- **Response** (`application/json`):

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "LoginResponse",
  "type": "object",
  "required": ["token", "user"],
  "properties": {
    "token": { "type": "string", "minLength": 16 },
    "user": {
      "type": "object",
      "required": ["id", "email", "fullName", "role"],
      "properties": {
        "id": { "type": "integer", "minimum": 1 },
        "email": { "type": "string", "format": "email" },
        "fullName": { "type": "string" },
        "role": { "type": "string" },
        "mustResetPassword": { "type": "boolean", "default": false }
      },
      "additionalProperties": false
    },
    "expiresAt": { "type": "string", "format": "date-time" }
  },
  "additionalProperties": false
}
```

### 3.2 `auth.logout`

- **Request**: Sin cuerpo (`204 No Content`).
- **Response** (`application/json`):

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "LogoutResponse",
  "type": "object",
  "properties": {
    "success": { "type": "boolean", "const": true }
  },
  "additionalProperties": false
}
```

### 3.3 `app.menu`

- **Request** (`application/json`):

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "MenuRequest",
  "type": "object",
  "properties": {
    "role": { "type": "string" },
    "includeShortcuts": { "type": "boolean", "default": false }
  },
  "additionalProperties": false
}
```

- **Response** (`application/json`):

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "MenuResponse",
  "type": "object",
  "required": ["items"],
  "properties": {
    "items": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["id", "text"],
        "properties": {
          "id": { "type": "string" },
          "text": { "type": "string" },
          "tooltip": { "type": "string" },
          "shortcut": { "type": "string" },
          "permission": { "type": "string" }
        },
        "additionalProperties": false
      }
    }
  },
  "additionalProperties": false
}
```

### 3.4 `app.bootstrap`

- **Request** (`application/json`):

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "BootstrapRequest",
  "type": "object",
  "properties": {
    "includeMenu": { "type": "boolean", "default": true },
    "includeBranding": { "type": "boolean", "default": true },
    "includeSession": { "type": "boolean", "default": true }
  },
  "additionalProperties": false
}
```

- **Response** (`application/json`):

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "BootstrapResponse",
  "type": "object",
  "properties": {
    "session": {
      "type": "object",
      "properties": {
        "token": { "type": "string" },
        "user": {
          "type": "object",
          "properties": {
            "id": { "type": "integer" },
            "email": { "type": "string", "format": "email" },
            "fullName": { "type": "string" },
            "role": { "type": "string" }
          },
          "additionalProperties": false
        }
      },
      "required": ["token", "user"],
      "additionalProperties": false
    },
    "branding": {
      "type": "object",
      "required": ["name"],
      "properties": {
        "name": { "type": "string" },
        "logoPath": { "type": "string" },
        "tagline": { "type": "string" }
      },
      "additionalProperties": false
    },
    "menu": { "$ref": "#/definitions/MenuResponse/items" },
    "features": {
      "type": "object",
      "properties": {
        "canAccessCustomers": { "type": "boolean" },
        "canAccessSales": { "type": "boolean" }
      },
      "additionalProperties": true
    }
  },
  "required": [],
  "additionalProperties": false,
  "definitions": {
    "MenuResponse": {
      "type": "object",
      "properties": {
        "items": {
          "type": "array",
          "items": { "$ref": "#/definitions/MenuItem" }
        }
      }
    },
    "MenuItem": {
      "type": "object",
      "required": ["id", "text"],
      "properties": {
        "id": { "type": "string" },
        "text": { "type": "string" },
        "tooltip": { "type": "string" },
        "shortcut": { "type": "string" },
        "permission": { "type": "string" }
      },
      "additionalProperties": false
    }
  }
}
```

## 4. Consideraciones de implementación

1. **Gestión de sesión**: El canal `auth.login` debe delegar en `authenticate` para asegurar la normalización de correo, verificación `bcrypt` y auditoría. El token generado (`Session.token`) puede reutilizarse como identificador de sesión en la capa de transporte.
2. **Menú dinámico**: Aprovechar `NavigationController` y `MenuItem` para serializar el estado de navegación. El adaptador IPC puede exponer sólo las acciones habilitadas según el rol (`Session.role`).
3. **Bootstrapping**: El endpoint `app.bootstrap` combina `get_current_session`, `get_branding` y un generador de menú. Este endpoint puede llamarse inmediatamente después de `auth.login` o en reanudaciones de sesión.
4. **Auditoría**: Todas las llamadas que cambien estado deben inyectar `actor` y `actor_id` usando `get_current_session()` como se hace en `customer_service`, manteniendo trazabilidad sin duplicar lógica.
5. **Extensibilidad**: Los esquemas pueden versionarse añadiendo el campo `contractVersion` en las respuestas si se requieren evoluciones futuras.

