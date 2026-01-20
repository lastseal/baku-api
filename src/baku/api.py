# -*- coding: utf-8 -*-

from flask import Flask
from flask import Request
from flask import request
from flask import abort
from flask import make_response
from flask import jsonify

from flask_cors import CORS

from gunicorn.app.base import Application, Config

from baku import config

import logging
import json
import jwt
import re
import functools

# Leer configuración desde variables de entorno usando baku-config
SECRET_KEY = config.get("SECRET_KEY")
UPLOAD_FOLDER = config.get("UPLOAD_FOLDER")
CORS_ENABLE = config.get("CORS_ENABLE", default="FALSE", converter=lambda x: x.upper() == "TRUE")
PORT = config.get("PORT", default="3000")
ADDRESS = config.get("ADDRESS", default="0.0.0.0")
WORKERS = config.get("WORKERS", default="1")
TIMEOUT = config.get("TIMEOUT", default="30")


class HttpRequest(Request):
    """Request extendido con parámetros, token y usuario."""

    def __init__(self, params, environ, token, user):
        super(HttpRequest, self).__init__(environ)
        self.params = params
        self.token = token
        self.user = user


class HttpServer(Application):
    """Servidor HTTP basado en Flask y Gunicorn."""

    def __init__(self):
        self.app = Flask(__name__)
        self.route_counter = 0

        if UPLOAD_FOLDER is not None:
            self.app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
            logging.info("upload folder: %s", UPLOAD_FOLDER)

        if CORS_ENABLE:
            self.cors = CORS(self.app)
            logging.info("CORS enabled")

        self.usage = None
        self.callable = None
        self.prog = None
        self.running = False
    
    def _register_route(self, method, endpoint, scope, handle_api):
        """Registra una ruta en Flask con validación de JWT y scope."""
        
        # Si la función tiene __scope__ definido, usar ese en lugar del parámetro
        if hasattr(handle_api, '__scope__'):
            scope = handle_api.__scope__
        
        # Si la función tiene __require_auth__ definido, usar ese para controlar auth
        require_auth = getattr(handle_api, '__require_auth__', None)
        
        logging.debug("config route %s %s", method, endpoint)
            
        def handle(**params):
            try:
                request_method = request.method
                if not request_method:
                    raise Exception({"message": "forbidden, error method", "status": 403})
                    
                token = None
                user = {}

                # Determinar si se requiere autenticación
                # Si require_auth es False explícitamente, no validar
                # Si require_auth es True o None y SECRET_KEY está configurado, validar
                should_validate = True
                if require_auth is False:
                    should_validate = False
                elif require_auth is True and SECRET_KEY is None:
                    raise Exception({"message": "forbidden, SECRET_KEY not configured", "status": 500})
                elif SECRET_KEY is None:
                    should_validate = False

                # Validar JWT si se requiere
                if should_validate and SECRET_KEY is not None:
                    # Usar request.path en lugar de request.url para evitar query params
                    endpoint_pattern = f"{request_method} {request.path}"

                    headers = request.headers
                    logging.debug("headers: %s", dict(headers))
                    
                    # Solo obtener token del header Authorization (eliminar query params)
                    if 'Authorization' in headers:
                        data = headers['Authorization'].split(' ')
                        logging.debug("Authorization: %s", data)

                        if len(data) != 2 or data[0] != "Bearer":
                            raise Exception({"message": "forbidden, error authorization", "status": 403})
                        
                        token = data[1]
                    else:
                        raise Exception({"message": "forbidden, error headers", "status": 403})

                    logging.debug("token: %s", token)
                    
                    # Decodificar JWT con manejo de excepciones
                    try:
                        user = jwt.decode(token, SECRET_KEY, algorithms="HS256")
                        logging.debug("JWT: %s", user)
                    except jwt.ExpiredSignatureError:
                        raise Exception({"message": "forbidden, token expired", "status": 403})
                    except jwt.InvalidTokenError as e:
                        logging.error("Invalid token: %s", e, exc_info=True)
                        raise Exception({"message": "forbidden, invalid token", "status": 403})
                    except Exception as e:
                        logging.error("Error decoding JWT: %s", e, exc_info=True)
                        raise Exception({"message": "forbidden, error decoding token", "status": 403})

                    # Validar scope
                    user_scopes = user.get('scopes', [])
                    
                    if scope is not None:
                        # Scope específico: buscar en lista de strings
                        allow = scope in user_scopes
                    else:
                        # Sin scope específico: validar por patrón si user_scopes es lista de dicts
                        if user_scopes and len(user_scopes) > 0 and isinstance(user_scopes[0], dict):
                            # Formato: lista de dicts con 'pattern'
                            allow = any(re.match(s.get('pattern', ''), endpoint_pattern) for s in user_scopes)
                        else:
                            # Formato: lista de strings, sin scope específico permite cualquier token válido
                            allow = True
                        
                    if not allow:
                        raise Exception({"message": "forbidden, error scope", "status": 403})

                # Ejecutar handler
                res = handle_api(HttpRequest(params, request.environ, token, user))

                # Serializar respuesta si es dict o list
                res_type = type(res)
                if res_type == dict or res_type == list:
                    return json.dumps(res)

                return res

            except Exception as ex:
                logging.error("Error processing request: %s", ex, exc_info=True)

                error = ex.args[0] if ex.args else None

                if type(error) == str:
                    status = 500
                    message = error
                elif isinstance(error, dict):
                    status = error.get('status', 500)
                    message = error.get('message', 'Internal server error')
                else:
                    status = 500
                    message = 'Internal server error'

                error_json = jsonify(message=message, status=status)

                return abort(make_response(error_json, status))

        unique_name = f"handle_{self.route_counter}"
        self.route_counter += 1
        self.app.add_url_rule(endpoint, unique_name, handle, methods=[method])
    
    def run(self):
        """Inicia el servidor Gunicorn."""
        if not self.running:
            self.running = True

            self.cfg = Config()

            self.cfg.set("worker_class", "gunicorn.workers.sync.SyncWorker")
            self.cfg.set("workers", WORKERS)
            self.cfg.set("threads", WORKERS)
            self.cfg.set("bind", f"{ADDRESS}:{PORT}")
            self.cfg.set("timeout", TIMEOUT)

            Application.run(self)
    
    def load(self):
        """Retorna la aplicación Flask (requerido por Gunicorn)."""
        return self.app


# Instancia global del servidor
server = HttpServer()

# Exponer la app Flask para compatibilidad
app = server.app


# Decoradores para control de autenticación
def scope(scope_value):
    """Decorador para especificar el scope requerido para una ruta.
    
    Args:
        scope_value: Scope requerido (string) o None para no requerir scope específico
    
    Ejemplo:
        @api.scope("read:users")
        @api.get("/api/users")
        def get_users(req):
            return {"users": []}
    """
    def decorator(func):
        func.__scope__ = scope_value
        func.__require_auth__ = True  # Si se especifica scope, requiere auth
        return func
    return decorator


def public(func):
    """Decorador para indicar que una ruta es pública (no requiere autenticación).
    
    Ejemplo:
        @api.public
        @api.get("/api/public")
        def public_handler(req):
            return {"message": "Público"}
    """
    func.__require_auth__ = False
    return func


# Decoradores a nivel de módulo
def get(endpoint, scope=None):
    """Decorador para método GET."""
    def decorator(handle_api):
        server._register_route("GET", endpoint, scope, handle_api)
        server.run()
        return handle_api
    return decorator


def post(endpoint, scope=None):
    """Decorador para método POST."""
    def decorator(handle_api):
        server._register_route("POST", endpoint, scope, handle_api)
        server.run()
        return handle_api
    return decorator


def put(endpoint, scope=None):
    """Decorador para método PUT."""
    def decorator(handle_api):
        server._register_route("PUT", endpoint, scope, handle_api)
        server.run()
        return handle_api
    return decorator


def delete(endpoint, scope=None):
    """Decorador para método DELETE."""
    def decorator(handle_api):
        server._register_route("DELETE", endpoint, scope, handle_api)
        server.run()
        return handle_api
    return decorator


def patch(endpoint, scope=None):
    """Decorador para método PATCH."""
    def decorator(handle_api):
        server._register_route("PATCH", endpoint, scope, handle_api)
        server.run()
        return handle_api
    return decorator

