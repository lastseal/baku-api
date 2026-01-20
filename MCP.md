# baku-api para Servicios MCP de Lastseal en la Nube

Este documento describe cómo usar `baku-api` en servicios MCP (Model Context Protocol) desplegados en Lastseal en la Nube para crear microservicios REST/API con un solo endpoint.

## Contexto

Los servicios MCP de Lastseal en la Nube frecuentemente requieren exponer endpoints HTTP/REST para:
- Integración con otros servicios
- Webhooks de sistemas externos
- APIs para clientes
- Procesamiento de datos mediante HTTP
- Endpoints de integración con sistemas legacy

El módulo `baku-api` proporciona un decorador simple y estandarizado para crear microservicios REST/API con un solo endpoint, incluyendo autenticación JWT opcional y validación de scopes.

## Instalación en Servicios MCP

### Requisitos

- Python 3.9 o superior
- Acceso al registry de GitHub Packages de Lastseal

### Instalación

```bash
# Configurar pip para usar GitHub Packages
pip install --upgrade pip
pip install keyring artifacts-keyring

# Instalar baku-api
pip install baku-api \
  --index-url https://pypi.org/simple \
  --extra-index-url https://USERNAME:TOKEN@pkg.github.com
```

O desde el repositorio:

```bash
pip install git+https://github.com/USERNAME/baku-api.git
```

## Uso en Servicios MCP

### Configuración Básica

```python
# Al inicio del servicio MCP
from baku import api

# El módulo automáticamente inicia el servidor al usar un decorador
@api.get("/api/endpoint")
def handler(req):
    return {"status": "ok"}
```

### Variables de Entorno

Los servicios MCP deben definir las siguientes variables de entorno (en `.env` o en el entorno de despliegue):

```bash
# Configuración del servidor (opcionales con valores por defecto)
PORT=3000              # Puerto del servidor (default: 3000)
ADDRESS=0.0.0.0        # Dirección de bind (default: 0.0.0.0)
WORKERS=1              # Número de workers de Gunicorn (default: 1)
TIMEOUT=30             # Timeout en segundos (default: 30)
UPLOAD_FOLDER=/uploads # Carpeta para uploads (opcional)
CORS_ENABLE=FALSE      # Habilitar CORS (default: FALSE)

# Autenticación JWT (opcional)
SECRET_KEY=your-secret-key  # Si está definido, habilita validación JWT
```

**Nota:** Si `SECRET_KEY` está definido, todas las rutas requerirán autenticación JWT mediante el header `Authorization: Bearer <token>`. Si no está definido, las rutas son públicas.

## Ejemplos de Uso en Servicios MCP

### Ejemplo 1: Endpoint Público Simple

```python
from baku import api
import logging

@api.get("/api/health")
def health_check(req):
    """Endpoint de health check."""
    logging.info("Health check solicitado")
    return {"status": "healthy", "service": "mcp-service"}
```

Con variable de entorno:
```bash
# Sin SECRET_KEY, el endpoint es público
PORT=8080
```

### Ejemplo 2: Endpoint con Autenticación JWT

```python
from baku import api
import logging

@api.get("/api/data")
def get_data(req):
    """Obtiene datos del usuario autenticado."""
    user_id = req.user.get('user_id')
    logging.info(f"Datos solicitados por usuario {user_id}")
    
    # Tu lógica aquí
    return {
        "user_id": user_id,
        "data": []
    }
```

Con variable de entorno:
```bash
SECRET_KEY=your-secret-key-here
PORT=8080
```

### Ejemplo 3: Endpoint con Scope Específico

```python
from baku import api
import logging

@api.scope("read:users")
@api.get("/api/users")
def get_users(req):
    """Obtiene lista de usuarios (requiere scope read:users)."""
    logging.info("Lista de usuarios solicitada")
    return {"users": []}
```

El token JWT debe incluir el scope:
```json
{
  "user_id": 123,
  "scopes": ["read:users", "write:users"]
}
```

### Ejemplo 4: Endpoint Público con Autenticación Habilitada

```python
from baku import api
import logging

@api.public
@api.get("/api/public")
def public_endpoint(req):
    """Endpoint público incluso con SECRET_KEY configurado."""
    logging.info("Endpoint público accedido")
    return {"message": "Este endpoint es público"}
```

### Ejemplo 5: POST con Body JSON

```python
from baku import api
import logging

@api.post("/api/process")
def process_data(req):
    """Procesa datos recibidos en el body."""
    data = req.json
    logging.info(f"Procesando datos: {data}")
    
    # Tu lógica de procesamiento aquí
    result = {"processed": True, "data": data}
    
    return result
```

### Ejemplo 6: Endpoint con Parámetros de Ruta

```python
from baku import api
import logging

@api.get("/api/users/<int:user_id>")
def get_user(req):
    """Obtiene un usuario específico por ID."""
    user_id = req.params['user_id']
    logging.info(f"Usuario {user_id} solicitado")
    
    # Tu lógica aquí
    return {"user_id": user_id, "name": "Example"}
```

### Ejemplo 7: Manejo de Errores

```python
from baku import api
import logging

@api.get("/api/find")
def find_resource(req):
    """Busca un recurso."""
    resource_id = req.args.get('id')
    
    if not resource_id:
        raise Exception({"status": 400, "message": "ID requerido"})
    
    # Si el recurso no existe
    if not resource_exists(resource_id):
        raise Exception({"status": 404, "message": "Recurso no encontrado"})
    
    return {"id": resource_id, "found": True}
```

## Consideraciones para Lastseal en la Nube

### Variables de Entorno en Producción

En Lastseal en la Nube, las variables de entorno se configuran a través del panel de control o archivos de configuración del servicio. El módulo `baku-api` las leerá automáticamente a través de `baku-config`.

**Recomendaciones:**
- Usar `SECRET_KEY` fuerte y seguro en producción
- Configurar `WORKERS` según la carga esperada (típicamente 2-4 workers por CPU)
- Habilitar `CORS_ENABLE=TRUE` solo si es necesario para integraciones web
- Configurar `UPLOAD_FOLDER` con permisos adecuados si se manejan uploads

### Logging en la Nube

El módulo `baku-api` usa el logging estándar de Python. Asegúrate de que `baku-config` esté configurado para logging consistente:

```python
from baku import config  # Configura logging automáticamente
from baku import api
import logging

@api.get("/api/endpoint")
def handler(req):
    logging.info("Endpoint accedido")  # Usa el logging configurado por baku-config
    return {"status": "ok"}
```

### Autenticación y Seguridad

**Generación de Tokens JWT:**

Los tokens JWT deben ser generados por otro servicio (por ejemplo, un servicio de autenticación) y deben incluir:

```python
import jwt

# Generar token con scopes
token = jwt.encode({
    "user_id": 123,
    "scopes": ["read:users", "write:users"]
}, SECRET_KEY, algorithm="HS256")
```

**Validación de Scopes:**

El módulo soporta dos formatos de scopes:

1. **Lista de strings** (para scope específico):
```json
{
  "user_id": 123,
  "scopes": ["read:users", "write:users"]
}
```

2. **Lista de diccionarios con patrones** (para validación por patrón):
```json
{
  "user_id": 123,
  "scopes": [
    {"pattern": "GET /api/users.*"},
    {"pattern": "POST /api/users.*"}
  ]
}
```

### Integración con Otros Servicios

El módulo está diseñado para microservicios con un solo endpoint. Para múltiples endpoints, considera:

- Usar múltiples servicios MCP (uno por endpoint)
- O usar un servicio MCP más complejo con múltiples decoradores (aunque esto no es el diseño recomendado)

### Performance y Recursos

- **Gunicorn**: El servidor usa Gunicorn con workers configurable
- **Un solo endpoint**: El diseño está optimizado para un microservicio simple con un solo endpoint
- **Bloqueo**: El decorador inicia el servidor automáticamente y bloquea el hilo principal (comportamiento esperado)

### Integración con PM2 / Systemd

El módulo inicia el servidor automáticamente al usar un decorador, lo cual es compatible con PM2 y systemd:

```python
# service.py
from baku import api

@api.get("/api/endpoint")
def handler(req):
    return {"status": "ok"}

# PM2/systemd ejecutará este script y el servidor se iniciará automáticamente
```

## Referencia de API

### Decoradores HTTP

#### `api.get(endpoint, scope=None)`

Registra un endpoint GET.

**Parámetros:**
- `endpoint` (str): Ruta del endpoint (puede incluir parámetros Flask como `<int:id>`)
- `scope` (str, opcional): Scope requerido para el endpoint

**Retorna:**
- `decorator`: Decorador que registra la ruta e inicia el servidor

**Ejemplo:**
```python
@api.get("/api/users", scope="read:users")
def get_users(req):
    return {"users": []}
```

#### `api.post(endpoint, scope=None)`

Registra un endpoint POST.

**Parámetros:** Igual que `api.get()`

**Ejemplo:**
```python
@api.post("/api/users")
def create_user(req):
    data = req.json
    return {"created": True, "data": data}
```

#### `api.put(endpoint, scope=None)`

Registra un endpoint PUT.

**Parámetros:** Igual que `api.get()`

#### `api.delete(endpoint, scope=None)`

Registra un endpoint DELETE.

**Parámetros:** Igual que `api.get()`

#### `api.patch(endpoint, scope=None)`

Registra un endpoint PATCH.

**Parámetros:** Igual que `api.get()`

### Decoradores de Autenticación

#### `api.scope(scope_value)`

Especifica el scope requerido para una ruta y habilita la autenticación.

**Parámetros:**
- `scope_value` (str): Scope requerido (ej: "read:users")

**Retorna:**
- `decorator`: Decorador que marca la función con el scope requerido

**Ejemplo:**
```python
@api.scope("read:users")
@api.get("/api/users")
def get_users(req):
    return {"users": []}
```

**Comportamiento:**
- Habilita autenticación JWT (requiere `SECRET_KEY`)
- Valida que el token tenga el scope especificado
- Si el token no tiene el scope, retorna 403

#### `api.public`

Indica que una ruta es pública (no requiere autenticación).

**Parámetros:** Ninguno

**Retorna:**
- `decorator`: Decorador que marca la función como pública

**Ejemplo:**
```python
@api.public
@api.get("/api/public")
def public_handler(req):
    return {"message": "Público"}
```

**Comportamiento:**
- Deshabilita autenticación JWT para esta ruta específica
- Funciona incluso si `SECRET_KEY` está configurado

### Objeto HttpRequest

El handler recibe un objeto `HttpRequest` que extiende `flask.Request`:

**Atributos disponibles:**

- `req.params` (dict): Parámetros de ruta (ej: `req.params['id']`)
- `req.args` (dict): Query parameters (ej: `req.args.get('page')`)
- `req.json` (dict): Body JSON para POST, PUT, PATCH
- `req.headers` (dict): Headers HTTP
- `req.token` (str): Token JWT decodificado (si `SECRET_KEY` está configurado)
- `req.user` (dict): Usuario decodificado del JWT (si `SECRET_KEY` está configurado)

**Ejemplo:**
```python
@api.get("/api/example/<int:id>")
def handler(req):
    # Parámetros de ruta
    id = req.params['id']
    
    # Query parameters
    page = req.args.get('page', default=1, type=int)
    
    # Token y usuario (si SECRET_KEY está configurado)
    user_id = req.user.get('user_id') if req.user else None
    
    return {"id": id, "page": page, "user_id": user_id}
```

### Comportamiento por Defecto de Autenticación

Si no usas ningún decorador de autenticación (`@api.scope()` o `@api.public`):

- **Si `SECRET_KEY` está configurado**: Todas las rutas requieren autenticación JWT
- **Si `SECRET_KEY` no está configurado**: Todas las rutas son públicas

## Troubleshooting

### El servidor no inicia

1. **Verificar variables de entorno:**
   ```bash
   echo $PORT
   echo $ADDRESS
   echo $SECRET_KEY
   ```

2. **Verificar logs:** El módulo registra información de inicio
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

3. **Verificar que el decorador esté aplicado:**
   ```python
   @api.get("/api/endpoint")  # El servidor se inicia automáticamente
   def handler(req):
       return {"status": "ok"}
   ```

### Error 403: "forbidden"

1. **Verificar que el token JWT sea válido:**
   - El token debe estar en el header: `Authorization: Bearer <token>`
   - El token debe ser válido según `SECRET_KEY`
   - El token no debe estar expirado

2. **Verificar scopes:**
   - Si usas `@api.scope()`, el token debe tener ese scope
   - Si usas validación por patrón, el token debe tener patrones que coincidan

3. **Verificar `SECRET_KEY`:**
   - Debe estar configurado si usas autenticación
   - Debe coincidir con el `SECRET_KEY` usado para generar el token

### Error 500: "Server misconfiguration: SECRET_KEY is not set"

- Ocurre cuando usas `@api.scope()` pero `SECRET_KEY` no está configurado
- Solución: Configurar `SECRET_KEY` o remover `@api.scope()`

### El endpoint no responde

1. **Verificar que la ruta esté registrada:**
   ```python
   # Verificar que el decorador esté aplicado correctamente
   @api.get("/api/endpoint")
   def handler(req):
       return {"status": "ok"}
   ```

2. **Verificar el método HTTP:**
   - Usa el método correcto (GET, POST, PUT, DELETE, PATCH)
   - Verifica que el endpoint coincida exactamente

3. **Verificar logs:** El módulo registra información de debug sobre las rutas

### CORS no funciona

1. **Verificar que `CORS_ENABLE=TRUE`:**
   ```bash
   echo $CORS_ENABLE
   ```

2. **Verificar que el módulo esté importado:**
   - `flask-cors` debe estar instalado
   - El módulo debe haberse importado correctamente

### Errores de serialización

- **Dict y List**: Se serializan automáticamente a JSON
- **String**: Se retorna como texto plano
- **Otros tipos**: Pueden causar errores, convertir a dict/list/string

## Ejemplo Completo de Servicio MCP

```python
#!/usr/bin/env python3
"""Servicio MCP de ejemplo usando baku-api para exponer un endpoint REST."""

from baku import config  # Configura logging y variables de entorno
from baku import api
import logging

# El módulo baku-config ya configuró logging y cargó .env automáticamente

@api.get("/api/status")
def get_status(req):
    """Endpoint de estado del servicio."""
    logging.info("Estado del servicio solicitado")
    
    # Obtener configuración
    service_name = config.get('SERVICE_NAME', default='mcp-service')
    
    return {
        "status": "running",
        "service": service_name,
        "version": "1.0.0"
    }

@api.scope("read:data")
@api.get("/api/data")
def get_data(req):
    """Obtiene datos (requiere autenticación con scope read:data)."""
    user_id = req.user.get('user_id')
    logging.info(f"Datos solicitados por usuario {user_id}")
    
    # Tu lógica aquí
    return {
        "user_id": user_id,
        "data": []
    }

@api.public
@api.post("/api/webhook")
def webhook_handler(req):
    """Endpoint público para webhooks."""
    data = req.json
    logging.info(f"Webhook recibido: {data}")
    
    # Procesar webhook
    # ...
    
    return {"received": True, "data": data}

# El servidor se inicia automáticamente al usar los decoradores
# No necesitas llamar a ninguna función explícitamente
```

Con variables de entorno:
```bash
# Configuración de baku-config
LOG_LEVEL=INFO

# Configuración de baku-api
PORT=8080
ADDRESS=0.0.0.0
WORKERS=2
TIMEOUT=30
CORS_ENABLE=TRUE

# Autenticación JWT
SECRET_KEY=your-secret-key-here

# Variables específicas del servicio
SERVICE_NAME=mcp-api-service
```

## Notas Importantes

- El módulo está diseñado para **un solo endpoint por servicio** (diseño de microservicio simple)
- El servidor se **inicia automáticamente** al usar cualquier decorador HTTP
- El servidor **bloquea el hilo principal** (comportamiento esperado para Gunicorn)
- Para múltiples endpoints, considera usar múltiples servicios MCP o un servicio más complejo
- El módulo es compatible con `baku-config` para logging y configuración estandarizada
- La autenticación JWT es opcional y se controla mediante `SECRET_KEY` y decoradores
- Los scopes pueden ser strings específicos o patrones regex según el formato del token


