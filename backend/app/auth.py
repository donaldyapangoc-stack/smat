from jose import jwt, JWTError
from datetime import datetime, timedelta
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer


SECRET_KEY = "UNMSM_FISI_SMAT_SECRET_2026"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Esquema para obtener token del header Authorization: Bearer <token>
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


USUARIOS_DB = {
    "admin_smat": {
        "username": "admin_smat",
        "password": "password123",
        "rol": "administrador"
    },
    "operador": {
        "username": "operador",
        "password": "smat_user2026",
        "rol": "lectura"
    }
}

def crear_token_acceso(data: dict):
    """Crea un token JWT con fecha de expiración"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def obtener_identidad_actual(token: str = Depends(oauth2_scheme)):
    """Valida el token y devuelve el username del usuario autenticado"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar el token de acceso",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        return username
    except JWTError:
        raise credentials_exception

def autenticar_usuario(username: str, password: str):
    """
    Verifica credenciales y retorna un token JWT si son correctas.
    Retorna None si las credenciales son inválidas.
    """
    usuario = USUARIOS_DB.get(username)
    if not usuario or usuario["password"] != password:
        return None
    
    # Crear token con los datos del usuario
    datos_token = {
        "sub": usuario["username"],
        "rol": usuario["rol"]
    }
    return crear_token_acceso(datos_token)