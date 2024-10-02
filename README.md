

## Entorno Python

### Version de Python
Python 3.11.5

### Inicializar entorno
Este comando de terminal crea un entorno virtual de Python en el directorio actual. Un entorno virtual es un espacio aislado donde puedes instalar paquetes de Python sin afectar a otros proyectos o al sistema Python global. .venv es el nombre del directorio donde se creará el entorno virtual.
```pwsh
python -m venv .venv
```

### Entrar en el entorno
Este comando de terminal activa el entorno virtual que acabas de crear. Cuando un entorno virtual está activo, cualquier paquete que instales con pip se instalará en ese entorno, no en el Python global. Esto es útil para mantener separadas las dependencias de diferentes proyectos. Debes ejecutar este comando cada vez que comiences a trabajar en este proyecto.
```pwsh
.venv\Scripts\activate
```

## Instalaciones
### Instalar librerias necesarias para Fast API
```pwsh
pip install fastapi uvicorn python-dotenv pymongo 
pip install "python-jose[cryptograpy]"
pip install "passlib[bcrypt]"
pip install python-multipart
```

## Iniciar servicio
### Servicio FastAPI
```pwsh
uvicorn main:app --reload
```