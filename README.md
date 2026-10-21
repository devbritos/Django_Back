# Sistema de Gestión de Resultados (SGR)

Aplicación web desarrollada con Django para apoyar el seguimiento de la gestión de funcionarios y delegaciones municipales de La Serena. Permite administrar información del personal, registrar actividades y evidencias, gestionar compromisos y consultar indicadores de avance.

Este proyecto fue desarrollado para la asignatura Programación Back End (TI3041), INACAP, sede La Serena.

## Funcionalidades

- Administración de funcionarios, delegaciones, cargos, roles y asignaciones de roles.
- Registro y seguimiento de actividades y sus evidencias, con un flujo de validación.
- Gestión de compromisos y sus fechas.
- Configuración de períodos, mediciones y metas.
- Paneles de seguimiento con indicadores para administración y funcionarios.
- Inicio de sesión y permisos según la cuenta y el rol.
- Páginas personalizadas para errores 403 y 404.

## Tecnologías

- Python
- Django 5.2
- MySQL o MariaDB
- `mysqlclient` para la conexión a la base de datos
- Bootstrap 5 y `django-crispy-forms` para los formularios

## Requisitos

- Python compatible con Django 5.2.
- MySQL o MariaDB en ejecución, con una base de datos creada para el proyecto.
- Git.

## Instalación local en Windows

1. Clona el repositorio y entra a su carpeta:

   ```powershell
   git clone https://github.com/devbritos/Django_Back.git
   cd Django_Back
   ```

2. Crea y activa un entorno virtual:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

3. Instala las dependencias:

   ```powershell
   python -m pip install -r requirements.txt
   ```

4. Crea un archivo `.env` en la raíz del proyecto con los datos de conexión a tu base de datos:

   ```dotenv
   DEBUG=True
   DB_NAME=nombre_de_la_base
   DB_USER=usuario_mysql
   DB_PASSWORD=contrasena_mysql
   DB_HOST=127.0.0.1
   DB_PORT=3306
   ```

   Reemplaza los valores de ejemplo por los de tu entorno. No compartas ni subas el archivo `.env` al repositorio.

5. Comprueba la configuración y crea las tablas:

   ```powershell
   python manage.py check
   python manage.py migrate
   ```

6. Crea una cuenta administradora para acceder al sistema:

   ```powershell
   python manage.py createsuperuser
   ```

7. Inicia el servidor de desarrollo:

   ```powershell
   python manage.py runserver
   ```

Abre `http://127.0.0.1:8000/` para entrar al sistema o `http://127.0.0.1:8000/admin/` para usar el administrador de Django.

## Secciones principales

| Sección | Ruta local | Descripción |
|---|---|---|
| Personal | `/personal/` | Funcionarios, delegaciones, cargos y roles |
| Actividades | `/activities/` | Actividades, evidencias y validación |
| Agenda | `/agenda/` | Compromisos |
| Configuración | `/configuration/` | Metas y períodos |
| Paneles | `/dashboard/` | Redirección al panel correspondiente al usuario |
| Administración Django | `/admin/` | Administración interna de Django |

## Aplicaciones Django

| Aplicación | Responsabilidad |
|---|---|
| `core` | Modelos y utilidades compartidas, incluidos los permisos |
| `personal` | Funcionarios, delegaciones, cargos, roles y sus asignaciones |
| `activities` | Actividades y evidencias |
| `agenda` | Compromisos |
| `configuration` | Períodos, mediciones y metas |
| `analytics` | Paneles e indicadores de seguimiento |

## Pruebas

Ejecuta la suite de pruebas con:

```powershell
python manage.py test
```

## Configuración y despliegue

La conexión actual requiere las variables `DB_NAME`, `DB_USER` y `DB_HOST`; `DB_PASSWORD` puede quedar vacío si la instalación local no usa contraseña y `DB_PORT` usa `3306` por defecto. El código carga variables desde `.env`.

`DEBUG` está desactivado por defecto si no se define en el entorno. Para desarrollo local se puede establecer en `True`; no debe habilitarse en producción. Antes de desplegar el sistema, configura una `SECRET_KEY` segura fuera del código, revisa `ALLOWED_HOSTS`, configura una base de datos adecuada y utiliza un servidor de producción. La clave secreta actualmente definida en la configuración es solo de desarrollo y debe reemplazarse antes de cualquier despliegue.

## Estructura del repositorio

```text
config/          Configuración y rutas principales de Django
core/            Componentes compartidos
personal/        Gestión del personal municipal
activities/      Actividades y evidencias
agenda/          Compromisos
configuration/   Períodos, mediciones y metas
analytics/       Paneles e indicadores
templates/       Plantillas HTML compartidas y páginas de error
static/          Archivos estáticos
```
