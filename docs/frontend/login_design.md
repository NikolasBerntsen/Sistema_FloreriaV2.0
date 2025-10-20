# Diseño de la vista de inicio de sesión

Este documento resume las decisiones visuales y los mockups de baja fidelidad para la vista de inicio de sesión del panel de la "Florería Carlitos". El objetivo es ofrecer una experiencia clara para usuarios administrativos que acceden desde el escritorio Electron.

## Tokens de diseño

Los tokens centralizan estilos para mantener consistencia entre componentes. Se implementaron en `desktop_app/frontend_electron/src/design/tokens.css` y `tokens.js`.

### Colores principales

| Token | Valor | Uso principal |
| --- | --- | --- |
| `--color-primary` | `#7C3AED` | Acciones primarias, degradados del logotipo |
| `--color-primary-dark` | `#5B21B6` | Estados `hover`, sombras pronunciadas |
| `--color-primary-soft` | `#EDE9FE` | Fondos neutrales, mensajes informativos |
| `--color-neutral-100` | `#FFFFFF` | Tarjetas y superficies elevadas |
| `--color-neutral-200` | `#F3F4F6` | Fondos secundarios, inputs |
| `--color-neutral-400` | `#9CA3AF` | Texto auxiliar y placeholders |
| `--color-neutral-600` | `#4B5563` | Texto secundario |
| `--color-neutral-900` | `#111827` | Texto principal |
| `--color-success` | `#16A34A` | Mensajes satisfactorios |
| `--color-danger` | `#DC2626` | Mensajes de error |

### Espaciados y radios

- Espaciado base: `--space-3 = 12px`.
- Padding principal de tarjetas: `--space-8 = 32px`.
- Radio estándar para controles: `--radius-sm = 8px`.
- Radio para tarjetas: `--radius-md = 16px`.
- Radio completo (`--radius-pill`) usado en el badge del logotipo.

### Tipografía y sombras

- Fuente base: Inter, con respaldo a `system-ui`.
- Jerarquía: títulos (`--font-size-title`), subtítulos (`--font-size-subtitle`), cuerpo (`--font-size-body`).
- Sombras: `--shadow-card` para tarjetas elevadas y `--shadow-button` para el botón primario al hacer hover.

## Mockups

> Los diagramas siguientes representan la estructura principal de la pantalla con espaciados relativos en unidades de token.

### Vista general (desktop 1280px)

```
┌──────────────────────────────────────────────┐
│                Fondo degradado               │
│                                              │
│      ┌──────────── Logo y título ─────────┐  │
│      │  [FC]  Florería Carlitos           │  │
│      │        Panel administrativo       │  │
│      └────────────────────────────────────┘  │
│                                              │
│      ┌────────────── Tarjeta ──────────────┐ │
│      │  Título "Inicia sesión"             │ │
│      │  Texto auxiliar                      │ │
│      │                                      │ │
│      │  Campo correo                        │ │
│      │  helper / error                      │ │
│      │                                      │ │
│      │  Campo contraseña                    │ │
│      │  helper / error                      │ │
│      │                                      │ │
│      │  Mensaje de estado (éxito/error)     │ │
│      │                                      │ │
│      │  Botón primario                      │ │
│      │  Enlace a soporte                    │ │
│      └──────────────────────────────────────┘ │
│                                              │
└──────────────────────────────────────────────┘
```

### Estados principales

- **Formulario inicial**: campos con placeholders y helper text gris (`--color-neutral-400`).
- **Validación**: mensajes en rojo (`--color-danger`) debajo del campo asociado.
- **Loading**: botón muestra `Verificando…` y se deshabilita.
- **Éxito**: tarjeta de estado con fondo verde claro (`rgba(22, 163, 74, 0.12)`) y texto `--color-success`.
- **Error**: tarjeta de estado con fondo rojo claro (`rgba(220, 38, 38, 0.12)`) y texto `--color-danger`.

## Reglas de interacción

1. Validación en cliente antes de enviar peticiones (correo y longitud mínima de contraseña).
2. Deshabilitar inputs y botón mientras se envía la petición.
3. Mostrar mensajes de estado con prioridad a errores del servidor.
4. Ofrecer CTA secundaria hacia soporte mediante `mailto`.

Estos lineamientos aseguran coherencia visual y técnica entre el mockup y la implementación React.
