# Aplicación de escritorio Florería Carlitos

Este directorio contiene el esqueleto de la aplicación de escritorio para Florería Carlitos, 
construida sobre Python y Tkinter. A continuación se describe el flujo recomendado para la 
instalación local, las variables de entorno necesarias y el proceso para generar un ejecutable 
para Windows.

## Requisitos previos

* Python 3.11 o superior.
* Acceso a un servidor MySQL accesible desde el equipo local.
* [pipx](https://pypa.github.io/pipx/) o `pip` para la instalación de dependencias.

## Instalación local

1. Clonar el repositorio y ubicarse en la carpeta `desktop_app/`:
   ```bash
   git clone <url-del-repo>
   cd Sistema_FloreriaV2.0/desktop_app
   ```
2. Crear y activar un entorno virtual (opcional pero recomendado):
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # En Windows usar .venv\Scripts\activate
   ```
3. Instalar las dependencias del proyecto:
   ```bash
   pip install -r requirements.txt
   ```
4. Configurar las variables de entorno descritas más abajo antes de ejecutar la aplicación.
5. Ejecutar la aplicación en modo desarrollo:
   ```bash
   python main.py
   ```

## Inicialización de la base de datos

El repositorio incluye scripts SQL de referencia en la carpeta `db/` para
crear el esquema principal, las extensiones de inventario y poblar datos
catálogo básicos. La secuencia recomendada es la siguiente:

```bash
mysql -u usuario -p floreriadb < db/schema.sql
mysql -u usuario -p floreriadb < db/extension.sql
mysql -u usuario -p floreriadb < db/seed.sql
```

Si se prefiere automatizar la verificación de tablas antes de ejecutar los
scripts, utilice el comando:

```bash
python -m app.db.migrate --user usuario --password ****** --host 127.0.0.1 --database floreriadb
```

El script `app.db.migrate` revisa la presencia de las tablas definidas en
`db/schema.sql` y `db/extension.sql`, ejecutando los archivos que falten en
el orden correcto y registrando el resultado en consola.

## Variables de entorno requeridas

La aplicación lee su configuración desde variables de entorno para localizar el archivo de 
configuración y establecer la conexión a la base de datos.

* `FLORERIA_CONFIG_PATH`: Ruta absoluta al archivo de configuración local (por ejemplo, un
  archivo INI con preferencias de la aplicación). Si no se establece, la aplicación iniciará
  con una configuración vacía.
* `FLORERIA_DB_DSN`: Cadena DSN con las credenciales de acceso a MySQL utilizando el formato
  `mysql://usuario:password@host:puerto/base_de_datos`. Se permiten parámetros adicionales como
  `?charset=utf8mb4`. Esta variable es obligatoria para iniciar la aplicación.

## Generar el ejecutable

1. Instalar PyInstaller (si aún no está disponible en el entorno):
   ```bash
   pip install pyinstaller
   ```
2. Ejecutar el script auxiliar para construir el ejecutable:
   ```bash
   python build_exe.py
   ```
3. El ejecutable `FloreriaCarlitos.exe` se ubicará en la carpeta `dist/` generada por PyInstaller.

## Creación del acceso directo en Windows

1. Copiar el archivo `FloreriaCarlitos.exe` generado en una carpeta destino (por ejemplo
   `C:\Program Files\FloreriaCarlitos`).
2. Hacer clic derecho sobre el ejecutable y seleccionar **Enviar a → Escritorio (crear acceso directo)**
   o crear manualmente un acceso directo en la ubicación deseada.
3. Abrir las propiedades del acceso directo y, en la sección **Inicio en**, establecer la ruta donde
   residen los archivos de configuración y recursos para asegurar que la aplicación encuentre los
   archivos necesarios.
4. (Opcional) Cambiar el icono del acceso directo utilizando un archivo `.ico` generado a partir de los
   recursos gráficos del proyecto (por ejemplo, usando `pillow`).

## Notas adicionales

* Para distribuir la aplicación en otros equipos, asegúrese de incluir instrucciones para configurar
  las variables de entorno `FLORERIA_CONFIG_PATH` y `FLORERIA_DB_DSN` (por ejemplo, mediante un script
  `.bat` que establezca las variables antes de lanzar el ejecutable).
* Mantenga segura la información de credenciales en el DSN. Considere usar usuarios de MySQL con
  privilegios limitados específicos para la aplicación.
