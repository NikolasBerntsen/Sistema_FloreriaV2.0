# Aplicación de escritorio Florería Carlitos (v2)

La solución de Florería Carlitos evoluciona hacia una interfaz moderna basada en
React + TypeScript empaquetada con Electron. El antiguo cliente Tkinter quedó en
estado de legado (consultar `docs/ui_inventory.md` para referencias históricas) y
ahora todo el flujo de autenticación, gestión de clientes y utilitarios CSV se
atiende desde `web_app/`.

La distribución final sigue orientada a usuarios de Windows a través de un único
instalador `.exe` generado con `electron-builder`, manteniendo la facilidad de uso
por medio de accesos directos al ejecutable.

## Requisitos

- Node.js 18 o superior (incluye `npm`).
- Acceso a la nueva API backend de Florería Carlitos (consultar documentación del
  servicio). Configure la URL base mediante la variable `VITE_API_BASE_URL`.
- Python 3.8+ opcionalmente, para utilizar `desktop_app/main.py` como lanzador o
  integrarlo en procesos existentes.

## Configuración inicial

1. Instalar dependencias del front-end:
   ```bash
   cd web_app
   npm install
   ```
2. Crear un archivo `.env` opcional en `web_app/` para personalizar variables:
   ```bash
   VITE_API_BASE_URL=https://api.floreriacarlitos.local
   ```
3. Ejecutar en modo desarrollo (Vite + Electron en caliente):
   ```bash
   npm run dev
   # o bien, desde la raíz del repo
   python desktop_app/main.py dev
   ```

El comando `python desktop_app/main.py` sin argumentos intenta localizar un
paquete ya construido (`dist-electron/`) y, en su defecto, abre la versión
estática (`dist/`) o lanza el modo desarrollo.

## Flujo de construcción y empaquetado

1. Generar la build de producción e instalador Windows:
   ```bash
   cd web_app
   npm run build:electron
   ```
2. El instalador (`Florería Carlitos Setup <versión>.exe`) y las variantes
   portables quedarán en `web_app/dist-electron/`.
3. Distribuir el instalador y crear un acceso directo habitual en el escritorio.

> **Sugerencia:** automatice la creación del acceso directo durante la instalación
> usando las opciones de NSIS incluidas en `electron-builder`.

## Estructura principal

- `web_app/`: código fuente React + TypeScript, providers para autenticación y
  notificaciones, rutas de clientes, utilidades CSV y scripts de empaquetado.
- `desktop_app/main.py`: lanzador multiplataforma que delega la ejecución al
  proyecto web (modo desarrollo o binarios empaquetados).
- `docs/ui_inventory.md`: inventario completo de pantallas heredadas en Tkinter
  que sirvió como base para alcanzar paridad funcional.
- `db/`: scripts SQL legados (mantener según necesidades de la nueva API).

## Configuración de la API

El cliente consume la API mediante peticiones autenticadas con bearer tokens.
Defina la variable `VITE_API_BASE_URL` antes de construir o ejecutar el proyecto
para apuntar al entorno deseado. Los servicios disponibles incluyen:

- `POST /auth/login`, `POST /auth/logout`, `GET /auth/me`.
- `GET /customers`, `POST /customers`, `PUT /customers/:id`,
  `POST /customers/:id/deactivate`.
- `GET /customers/:id/summary`, `GET /customers/export`,
  `POST /customers/import` (`mode=preview|commit`).

Las respuestas de error son surfaced al usuario con notificaciones equivalentes a
los `messagebox` de la interfaz Tkinter.

## Desarrollo colaborativo

- Correr `npm run lint` y `npm run typecheck` para validar el código TypeScript.
- Utilizar `npm run dev` durante el desarrollo para aprovechar recarga en vivo.
- Actualizar las notas de despliegue en esta guía si se añaden nuevos módulos o
  cambia la configuración requerida.

## Migración desde la versión Tkinter

1. Revise `docs/ui_inventory.md` para identificar la correspondencia de vistas.
2. Elimine instaladores previos generados con PyInstaller y reemplace los accesos
   directos por el nuevo instalador Electron.
3. Mantenga el backend actualizado y asegure compatibilidad con los contratos
   de la API mencionados arriba.

Con esta estructura, el proyecto puede seguir empaquetándose en un `.exe`
único, respetando la experiencia de un doble clic para abrir la aplicación.
