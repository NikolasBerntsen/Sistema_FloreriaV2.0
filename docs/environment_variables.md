# Variables de entorno de Florería Carlitos

Este documento detalla cada una de las variables de entorno que la aplicación de escritorio utiliza para inicializarse correctamente. Las variables pueden definirse en el sistema operativo, en un archivo `.env` cargado por el shell o en el gestor de procesos utilizado para ejecutar la aplicación. A partir de la versión actual, el archivo `.env` que se encuentre en la raíz del proyecto se cargará automáticamente durante el arranque si está disponible la dependencia `python-dotenv`.

## Tabla resumen

| Variable | Obligatoria | Descripción |
| --- | --- | --- |
| `FLORERIA_DB_DSN` | Sí | Cadena DSN con las credenciales y el host de MySQL. |
| `FLORERIA_CONFIG_PATH` | No | Ruta a un archivo INI con ajustes locales opcionales. |
| `DB_HOST` | No* | Host del servidor MySQL usado por `app/db/migrate.py`. |
| `DB_PORT` | No* | Puerto del servidor MySQL usado por `app/db/migrate.py`. |
| `DB_USER` | No* | Usuario MySQL usado por `app/db/migrate.py`. |
| `DB_PASSWORD` | No* | Contraseña MySQL usada por `app/db/migrate.py`. |
| `DB_NAME` | No* | Base de datos objetivo usada por `app/db/migrate.py`. |
| `FLORERIA_BRAND_NAME` | No | Nombre comercial que se mostrará en la interfaz. |
| `FLORERIA_BRAND_LOGO` | No | Ruta a una imagen PNG/GIF utilizada como logotipo. |
| `FLORERIA_BRAND_TAGLINE` | No | Eslogan o texto secundario mostrado en la cabecera. |

\*Las variables `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD` y `DB_NAME` son necesarias únicamente cuando se ejecuta el script de migraciones `python -m app.db.migrate`. La aplicación de escritorio consume la cadena `FLORERIA_DB_DSN` para conectarse a la base de datos.

## Descripción detallada

### `FLORERIA_DB_DSN`

* **Tipo:** Cadena.
* **Formato:** `mysql://usuario:contraseña@host:puerto/base_de_datos?parametros_opcionales`.
* **Ejemplo:** `mysql://floreria:superseguro@127.0.0.1:3306/floreriadb?charset=utf8mb4`.
* **Uso:** `desktop_app/main.py` convierte el DSN en parámetros para `mysql.connector.connect`. Es obligatoria; si falta o no respeta el esquema `mysql`, el arranque se interrumpe.

### `FLORERIA_CONFIG_PATH`

* **Tipo:** Ruta absoluta o relativa.
* **Ejemplo:** `/etc/floreria/app.ini`.
* **Uso:** Si se define, la aplicación carga el archivo INI para ajustar comportamientos locales (por ejemplo, branding). Si no está definida o el archivo no existe, se utiliza una configuración vacía.

### Variables auxiliares para migraciones (`DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`)

* **Tipo:**
  * `DB_HOST`: Cadena con el hostname o IP (por defecto `127.0.0.1`).
  * `DB_PORT`: Entero (por defecto `3306`).
  * `DB_USER`: Cadena con el usuario (por defecto `root`).
  * `DB_PASSWORD`: Cadena con la contraseña (sin valor por defecto, se solicita si falta).
  * `DB_NAME`: Cadena con el nombre de la base de datos (por defecto `floreriadb`).
* **Uso:** El script de migraciones (`desktop_app/app/db/migrate.py`) permite sobrescribir sus argumentos con estas variables de entorno para facilitar la automatización.

### `FLORERIA_BRAND_NAME`

* **Tipo:** Cadena.
* **Ejemplo:** `Florería Las Rosas`.
* **Uso:** Sobrescribe el nombre comercial calculado a partir del archivo de configuración. Se muestra en la barra de título, cabecera y vistas principales.

### `FLORERIA_BRAND_LOGO`

* **Tipo:** Ruta a un archivo de imagen compatible con Tk (`.png`, `.gif`, `.ppm`).
* **Ejemplo:** `/opt/floreria/branding/logo.png`.
* **Uso:** Permite mostrar un logotipo personalizado en la barra superior de la interfaz. Si la ruta no existe o el archivo no es compatible, se ignora de forma segura.

### `FLORERIA_BRAND_TAGLINE`

* **Tipo:** Cadena.
* **Ejemplo:** `Flores frescas todos los días`.
* **Uso:** Texto secundario que se renderiza bajo el nombre comercial en la cabecera. Ayuda a reforzar la identidad de marca.

## Recomendaciones

* Mantén las credenciales en un gestor seguro (por ejemplo, `keyring`, `pass` o variables de entorno definidas por el sistema).
* Evita versionar archivos que contengan secretos reales (como `app.ini` o `.env`).
* Para entornos de producción, utiliza conexiones TLS configurando los parámetros adicionales en el DSN (`ssl_ca`, `ssl_cert`, `ssl_key`).
