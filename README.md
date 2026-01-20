# baku-api

Módulo que permite crear micro servicios REST/API con un solo endpoint.

## Instalación

### Desde GitHub Packages

Primero, configura pip para usar GitHub Packages creando o editando `~/.pip/pip.conf` (Linux/Mac) o `%APPDATA%\pip\pip.ini` (Windows):

```ini
[global]
extra-index-url = https://USERNAME:TOKEN@pkg.github.com
```

Luego instala el paquete:

```bash
pip install baku-api
```

### Desde el repositorio (desarrollo)

```bash
pip install git+https://github.com/USERNAME/baku-api.git
```

Nota: Reemplaza `USERNAME` con tu usuario de GitHub y `TOKEN` con un Personal Access Token con permisos de lectura de paquetes.

## Configuración

### Variables de Entorno

El módulo usa `baku-config` para leer variables de entorno. Configúralas en `.env` o en el entorno de despliegue:

```bash
# Opcionales (con valores por defecto)
PORT=3000              # Puerto del servidor (default: 3000)
ADDRESS=0.0.0.0        # Dirección de bind (default: 0.0.0.0)
WORKERS=1              # Número de workers de Gunicorn (default: 1)
TIMEOUT=30             # Timeout en segundos (default: 30)
UPLOAD_FOLDER=/uploads # Carpeta para uploads (opcional)
CORS_ENABLE=FALSE      # Habilitar CORS (default: FALSE)

# Opcional: JWT Authentication
SECRET_KEY=your-secret-key  # Si está definido, habilita validación JWT
```

**Nota:** Si `SECRET_KEY` está definido, todas las rutas requerirán autenticación JWT mediante el header `Authorization: Bearer <token>`. Si no está definido, las rutas son públicas.

## Uso Básico

### Endpoint Simple

```python
from baku import api

@api.get("/api/hello")
def main(req):
    return "Hello World"
```

### Con Parámetros de Ruta

```python
from baku import api

@api.get("/api/<int:id>")
def main(req):
    return f"id={req.params['id']}"
```

### Con Query Parameters

```python
from baku import api

@api.get("/api/find")
def main(req):
    id = req.args.get('id')
    return {"id": id}
```

### Retornar JSON

```python
from baku import api

@api.get("/api/data")
def main(req):
    return {
        "id": 1,
        "name": "Example"
    }
```

### POST con Body JSON

```python
from baku import api

@api.post("/api/update")
def main(req):
    data = req.json
    return {"data": data}
```

### Manejo de Errores

```python
from baku import api

@api.get("/api/find")
def main(req):
    raise Exception({"status": 400, "message": "Error de usuario"})
```

### Iniciar el Servidor

El servidor se inicia automáticamente cuando se usa cualquier decorador:

```python
from baku import api

@api.get("/api/hello")
def main(req):
    return "Hello World"

# El servidor se inicia automáticamente al usar el decorador
```

## Autenticación JWT

### Control de Autenticación con Decoradores

Puedes controlar la autenticación usando decoradores antes del decorador HTTP:

#### Decorador `@api.scope()`

Especifica el scope requerido y habilita la autenticación:

```python
from baku import api

@api.scope("read:users")
@api.get("/api/users")
def get_users(req):
    return {"users": []}
```

#### Decorador `@api.public`

Indica que la ruta es pública (no requiere autenticación):

```python
from baku import api

@api.public
@api.get("/api/public")
def public_handler(req):
    return {"message": "Público"}
```

#### Comportamiento por Defecto

Si no usas ningún decorador de autenticación:
- Si `SECRET_KEY` está configurado: requiere autenticación
- Si `SECRET_KEY` no está configurado: ruta pública

### Validación de Token

Si se requiere autenticación (por `@api.scope()` o por tener `SECRET_KEY` configurado), todas las rutas requieren autenticación JWT.

### Formato del Token

El token debe enviarse en el header:

```
Authorization: Bearer <token>
```

### Validación de Scope

El módulo soporta validación de scopes de dos formas:

#### 1. Scope Específico

```python
from baku import api

@api.get("/api/users", scope="read:users")
def get_users(req):
    # Solo se ejecuta si el token tiene el scope "read:users"
    return {"users": []}
```

El token JWT debe tener un campo `scopes` con una lista de strings:

```json
{
  "user_id": 123,
  "scopes": ["read:users", "write:users"]
}
```

#### 2. Scope por Patrón

Si no se especifica un scope, el módulo valida usando patrones regex:

```python
from baku import api

@api.get("/api/users")
def get_users(req):
    # Valida usando patrones en user['scopes']
    return {"users": []}
```

El token JWT debe tener un campo `scopes` con una lista de diccionarios:

```json
{
  "user_id": 123,
  "scopes": [
    {"pattern": "GET /api/users.*"},
    {"pattern": "POST /api/users.*"}
  ]
}
```

## Métodos HTTP Disponibles

- `@api.get(endpoint, scope=None)` - GET
- `@api.post(endpoint, scope=None)` - POST
- `@api.put(endpoint, scope=None)` - PUT
- `@api.delete(endpoint, scope=None)` - DELETE
- `@api.patch(endpoint, scope=None)` - PATCH

## Objeto Request

El handler recibe un objeto `HttpRequest` que extiende `flask.Request`:

```python
@api.get("/api/example")
def handler(req):
    # Parámetros de ruta
    id = req.params.get('id')
    
    # Query parameters
    page = req.args.get('page')
    
    # Body JSON (para POST, PUT, PATCH)
    data = req.json
    
    # Headers
    content_type = req.headers.get('Content-Type')
    
    # Token JWT (si SECRET_KEY está configurado)
    token = req.token
    
    # Usuario decodificado del JWT (si SECRET_KEY está configurado)
    user = req.user
    user_id = req.user.get('user_id')
    
    return {"status": "ok"}
```

## Ejecutar Tests

```bash
# Instalar dependencias de desarrollo
pip install pytest pytest-cov

# Ejecutar tests
pytest

# Con cobertura
pytest --cov=baku --cov-report=html
```

## Dependencias

- `Flask>=1.1.2` - Framework web
- `Flask-Cors>=4.0.1` - Soporte CORS
- `gunicorn>=20.0.4` - Servidor WSGI
- `pyjwt>=2.1.0` - Validación JWT
- `baku-config>=1.0.0` - Configuración y logging estandarizado

