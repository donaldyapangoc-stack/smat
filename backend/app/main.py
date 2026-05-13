from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware  #Continuando Desarrollo en Windows 
from sqlalchemy.orm import Session
from pydantic import BaseModel
from . import models              
from .database import engine, get_db
from . import schemas

# ==========================================================
# CRITICAL: CREACIÓN DE LA BASE DE DATOS Y TABLAS
# Esta línea busca el archivo 'smat.db' y crea las tablas
# definidas en models.py si es que aún no existen.
# ==========================================================
models.Base.metadata.create_all(bind=engine)
app = FastAPI(
    title="SMAT - Sistema de Monitoreo de Alerta Temprana",
    description="""
    API robusta para la gestión y monitoreo de desastres naturales.
    Permite la telemetría de sensores en tiempo real y el cálculo de niveles de riesgo.
    **Entidades principales:**
    * **Estaciones:** Puntos de monitoreo físico.
    * **Lecturas:** Datos capturados por sensores.
    * **Riesgos:** Análisis de criticidad basado en umbrales.
    """,
    version="1.0.0",
    terms_of_service="http://unmsm.edu.pe/terms/",
    contact={
        "name": "Soporte Técnico SMAT - FISI",
        "url": "http://fisi.unmsm.edu.pe",
        "email": "desarrollo.smat@unmsm.edu.pe",
    },
    license_info={
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
    },
)

#Para cuando este desarrollando en Windows :p
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Esquemas de validación (Pydantic)
class EstacionCreate(BaseModel):
    id: int
    nombre: str
    ubicacion: str  
class LecturaCreate(BaseModel):
    estacion_id: int
    valor: float


@app.post(
    "/estaciones/",
    status_code=201,
    tags=["Gestión de Infraestructura"],
    summary="Registrar una nueva estación de monitoreo",
    description="Inserta una estación física (ej. río, volcán, zona sísmica) en la base de datos relacional."
)
def crear_estacion(estacion: schemas.EstacionCreate, db: Session = Depends(get_db)):
    #Logica implementada en S2 y S3
    # Convertimos el esquema de Pydantic a Modelo de SQLAlchemy
    nueva_estacion = models.EstacionDB(id=estacion.id, nombre=estacion.nombre,
    ubicacion=estacion.ubicacion)
    db.add(nueva_estacion)
    db.commit()
    db.refresh(nueva_estacion)
    return {"msj": "Estación guardada en DB", "data": nueva_estacion}

@app.get("/estaciones/")
async def listar_estaciones(db: Session = Depends(get_db)):
    estaciones = db.query(models.EstacionDB).all()
    return estaciones

class Lectura(BaseModel):
    estacion_id: int
    valor: float

db_lecturas = []

@app.post(
"/lecturas/",
    status_code=201,
    tags=["Telemetría de Sensores"],
    summary="Recibir datos de telemetría",
    description="Recibe el valor capturado por un sensor y lo vincula a una estación existente mediante su ID."
)
def registrar_lectura(lectura: schemas.LecturaCreate, db: Session = Depends(get_db)):
    #   ... (lógica implementada)
    # Validar si la estación existe en la DB
    estacion = db.query(models.EstacionDB).filter(models.EstacionDB.id ==
    lectura.estacion_id).first()
    if not estacion:
            raise HTTPException(status_code=404, detail="Estación no existe")
    nueva_lectura = models.LecturaDB(valor=lectura.valor,
    estacion_id=lectura.estacion_id)
    db.add(nueva_lectura)
    db.commit()
    return {"status": "Lectura guardada en DB"}

@app.get(
    "/estaciones/{id}/riesgo",
    tags=["Análisis de Riesgo"],
    summary="Evaluar nivel de peligro actual",
    description="Analiza la última lectura recibida de una estación y determina si el estado es NORMAL, ALERTA o PELIGRO."
)
async def obtener_riesgo(id: int, db: Session = Depends(get_db)):
    # 1. Validar existencia de la estación
    estacion = db.query(models.EstacionDB).filter(models.EstacionDB.id == id).first()
    if not estacion:
        raise HTTPException(status_code=404, detail="Estación no encontrada")
    
    # 2. Filtrar lecturas de la estación
    lecturas = db.query(models.LecturaDB).filter(models.LecturaDB.estacion_id == id).all()
    if not lecturas:
        return {"id": id, "nivel": "SIN DATOS", "valor": 0}
    
    # 3. Evaluar última lectura
    ultima_lectura = lecturas[-1].valor
    if ultima_lectura > 20.0:
        nivel = "PELIGRO"
    elif ultima_lectura > 10.0:
        nivel = "ALERTA"
    else:
        nivel = "NORMAL"
    return {"id": id, "valor": ultima_lectura, "nivel": nivel}


@app.get("/estaciones/{id}/historial")
async def obtener_historial(id: int, db: Session = Depends(get_db)):
    # PASO 1: Verificar si la estación existe
    estacion = db.query(models.EstacionDB).filter(models.EstacionDB.id == id).first()
    if not estacion:
        raise HTTPException(status_code=404, detail="Estación no encontrada")

    # PASO 2: Filtrar las lecturas
    lecturas = db.query(models.LecturaDB).filter(models.LecturaDB.estacion_id == id).all()
    valores_lecturas = [lectura.valor for lectura in lecturas]

    # PASO 3: Calcular el promedio
    if len(valores_lecturas) > 0:
        promedio = sum(valores_lecturas) / len(valores_lecturas)
    else:
        promedio = 0.0

    # PASO 4: Retornar el JSON
    return {
        "estacion_id": id,
        "lecturas": valores_lecturas,
        "conteo": len(valores_lecturas),
        "promedio": round(promedio, 2)
    }