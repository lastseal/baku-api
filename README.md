# Baku Collections
![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)

## Instalación

```bash
pip install git+https://github.com/lastseal/baku-api
```

## Ejemplos

Lectura de registros de una colección. En el ejemplo, el nombre de la colección es ```pruebas``` y la estrucuta del registro JSON es el siguiente:

```json
{
    "name": "nombre de la prueba",
    "list": ["data1", "data2"],
    "object": {
        "flag": true,
        "channel": "test"
    }
}
```

Se busca la prueba de nombre ```test-1``` con la variable ```name``` del registro.

```python
from baku import api

pruebas = api.Collection("pruebas")

data = prueba.findOne({"name": "test-1"})
print("name:", data.name)
print("list.0:", data.list[0])
print("object.flag:", data.object['flag'])
```