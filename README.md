# Django_Back
Project of Back-end Linked to Integrated-Project :) 

# Sistema de Gestión de Resultados (SGR)

Proyecto de Programación Back End (TI3041), INACAP sede La Serena. Es una aplicación web en Django para registrar y medir la gestión de funcionarios y delegaciones municipales, trabajada principalmente desde el Django Admin.

**Integrantes:** [Nombre 1], [Nombre 2]
**Sección:** [sección]
**Docente:** Javier Ahumada

## Qué hace el sistema

Cada funcionario pertenece a una delegación y tiene un cargo y uno o más roles. Para cada cargo y período se definen metas sobre mediciones. Los funcionarios registran actividades con sus evidencias, que un verificador aprueba o rechaza, y también compromisos con fecha. Solo las evidencias aprobadas cuentan para el avance.

## Requisitos

- Python 3.11
- Git

## Instalación

1. Clonar el repositorio:

```bash
git clone https://github.com/devbritos/Django_Back.git
cd Django_Back
```

2. Crear y activar el entorno virtual:

```bash
python -m venv .venv
.venv\Scripts\activate
```

En Linux o Mac se activa con `source .venv/bin/activate`.

3. Instalar las dependencias:

```bash
pip install -r requirements.txt
```

4. Crear el archivo `.env` a partir del ejemplo:

```bash
copy .env.example .env
```

En Linux o Mac: `cp .env.example .env`. Después se abre `.env` y se completan los valores (ver la sección siguiente).

5. Revisar el proyecto y aplicar las migraciones:

```bash
python manage.py check
python manage.py migrate
```

6. Cargar los datos de prueba:

```bash
python manage.py seed_data
```

7. Levantar el servidor:

```bash
python manage.py runserver
```

El Admin queda en http://127.0.0.1:8000/admin/

## Variables de entorno

La configuración sensible no está en el código, `settings.py` la lee desde `.env`. El archivo `.env` no se sube al repositorio, solo `.env.example`.

| Variable | Para qué sirve | Ejemplo |
|---|---|---|
| SECRET_KEY | Clave secreta de Django | una cadena larga y aleatoria |
| DEBUG | Modo desarrollo | True |
| ALLOWED_HOSTS | Hosts permitidos | 127.0.0.1,localhost |
| DB_ENGINE | Motor de base de datos | django.db.backends.sqlite3 |
| DB_NAME | Nombre o ruta de la base | db.sqlite3 |

Para usar otro motor (por ejemplo PostgreSQL) se cambian `DB_ENGINE` y `DB_NAME` y se agregan `DB_USER`, `DB_PASSWORD`, `DB_HOST` y `DB_PORT`, sin tocar el código.

## Cuentas de prueba

Son cuentas ficticias, solo para la demostración.

| Usuario | Contraseña | Rol | Qué puede hacer |
|---|---|---|---|
| [admin_sgr] | [contraseña] | Administrador | Ve y modifica todo |
| [usuario_limitado] | [contraseña] | Usuario limitado | Solo ve los datos de su delegación |

## Estructura del proyecto

Cada app tiene una responsabilidad del dominio:

| App | Responsabilidad |
|---|---|
| core | `BaseModel` abstracto con `created_at`, `updated_at` y `deleted_at`, del que heredan las entidades principales |
| personal | Delegation, Position, Role, Functionary, FunctionaryRole |
| configuration | Period, Measuring, Goal (períodos, qué se mide y metas por cargo) |
| agenda | Commitment (compromisos con fecha y estado) |
| activities | Activity y Evidence (trabajo realizado y su evidencia) |
| auditory | Registro de auditoría de operaciones |
| analytics | Sin tablas propias, reservada para los cálculos de avance, cumplimiento y semáforo |

En cada app, `models.py` tiene los modelos y `admin.py` la configuración del Admin. Los nombres de modelos y atributos están en inglés.

## Funcionalidades del Admin

- **Admin básico:** todos los modelos tienen `list_display`, `search_fields`, `list_filter` y `ordering`, y `list_select_related` donde la lista muestra relaciones.
- **Inline:** los roles de un funcionario se asignan dentro de su propia pantalla (`FunctionaryRole`), y las evidencias se agregan dentro de cada actividad (`Evidence`).
- **Acción personalizada:** "Approve selected evidences" aprueba varias evidencias a la vez y actualiza su fecha de validación.
- **Validación:** `Period.clean()` rechaza un período cuya fecha de término sea anterior a la de inicio, o con más días computables que los del período.

## Seguridad

[Completar cuando esté implementado: explicar cómo el usuario limitado solo ve registros de su delegación y en qué archivo se aplica la restricción.]

## Trabajo con Git

- `main`: versión final entregada.
- `develop`: integración del trabajo del equipo.
- `feature/*`: una rama por funcionalidad (por ejemplo `feature/personal-models`, `feature/personal-admin`, `feature/configuration-admin`), que se integra a `develop` con merge.

El `.env` y `.venv` están en `.gitignore` y no se suben.

**Commit final evaluado:** [hash]
