from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware  
from sqlalchemy.orm import Session
from pydantic import BaseModel
from . import models              
from .database import engine, get_db
from . import schemas
from fastapi.security import OAuth2PasswordRequestForm
from .auth import crear_token_acceso, obtener_identidad_actual


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
    description="Inserta una estación física en la base de datos. Requiere autenticación JWT."
)
def crear_estacion(
    estacion: schemas.EstacionCreate,
    db: Session = Depends(get_db),
    usuario: str = Depends(obtener_identidad_actual)
):
   #ID autogenerada
    nueva_estacion = models.EstacionDB(
        nombre=estacion.nombre,
        ubicacion=estacion.ubicacion
    )
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
    description="""Recibe el valor capturado por un sensor.
    
    **Validaciones:**
    - Requiere autenticación JWT (Bearer Token)
    - Verifica que la estación exista antes de guardar
    """
)
def registrar_lectura(
    lectura: schemas.LecturaCreate,
    db: Session = Depends(get_db),
    usuario: str = Depends(obtener_identidad_actual)  
):
    estacion_db = db.query(models.EstacionDB).filter(
        models.EstacionDB.id == lectura.estacion_id
    ).first()
    
    if not estacion_db:
        raise HTTPException(
            status_code=404,
            detail="Error de Integridad: La estación no existe en la base de datos."
        )
    
    # Si la estación existe, guardar la lectura
    nueva_lectura = models.LecturaDB(
        valor=lectura.valor,
        estacion_id=lectura.estacion_id
    )
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

@app.get(
    "/estaciones/stats",
    tags=["Estadísticas"],
    summary="Resumen Ejecutivo del Sistema SMAT",
    description="""Resumen ejecutivo del sistema de monitoreo SMAT.
    
    Este endpoint proporciona una visión general del estado del sistema,
    incluyendo métricas clave para la toma de decisiones.
    """
)
async def estadisticas_estaciones(db: Session = Depends(get_db)):
    """
    RESUMEN EJECUTIVO - SMAT Monitoreo de Alerta Temprana
    
    Este reporte muestra un panorama completo del estado actual del sistema,
    permitiendo a los gestores evaluar rápidamente la situación.
    """
    # Contar total de estaciones
    total_estaciones = db.query(models.EstacionDB).count()
    
    # Contar total de lecturas registradas
    total_lecturas = db.query(models.LecturaDB).count()
    
    # Calcular riesgo por estación
    estaciones_riesgo = []
    estaciones = db.query(models.EstacionDB).all()
    
    estaciones_peligro = 0
    estaciones_alerta = 0
    estaciones_normal = 0
    estaciones_sin_datos = 0
    
    for estacion in estaciones:
        ultima_lectura = db.query(models.LecturaDB)\
            .filter(models.LecturaDB.estacion_id == estacion.id)\
            .order_by(models.LecturaDB.id.desc())\
            .first()
        
        if not ultima_lectura:
            estaciones_sin_datos += 1
            nivel = "SIN DATOS"
        elif ultima_lectura.valor > 20.0:
            estaciones_peligro += 1
            nivel = "PELIGRO"
        elif ultima_lectura.valor > 10.0:
            estaciones_alerta += 1
            nivel = "ALERTA"
        else:
            estaciones_normal += 1
            nivel = "NORMAL"
        
        estaciones_riesgo.append({
            "id": estacion.id,
            "nombre": estacion.nombre,
            "nivel": nivel,
            "ultima_lectura": ultima_lectura.valor if ultima_lectura else None
        })
    
    # Calcular promedio general de lecturas
    todas_lecturas = db.query(models.LecturaDB.valor).all()
    promedio_general = sum(l[0] for l in todas_lecturas) / len(todas_lecturas) if todas_lecturas else 0
    
    return {
        "resumen_ejecutivo": {
            "total_estaciones": total_estaciones,
            "total_lecturas": total_lecturas,
            "promedio_general_lecturas": round(promedio_general, 2),
            "estadisticas_riesgo": {
                "en_peligro": estaciones_peligro,
                "en_alerta": estaciones_alerta,
                "normal": estaciones_normal,
                "sin_datos": estaciones_sin_datos
            }
        },
        "detalle_estaciones": estaciones_riesgo,
        "recomendaciones": _generar_recomendaciones(estaciones_peligro, estaciones_alerta)
    }

def _generar_recomendaciones(peligro, alerta):
    recomendaciones = []
    if peligro > 0:
        recomendaciones.append(f"🚨 ATENCIÓN: {peligro} estación(es) en nivel PELIGRO requieren intervención inmediata")
    if alerta > 0:
        recomendaciones.append(f"⚠️ PRECAUCIÓN: {alerta} estación(es) en nivel ALERTA requieren monitoreo")
    if peligro == 0 and alerta == 0:
        recomendaciones.append("✅ Todas las estaciones operan dentro de parámetros normales")
    return recomendaciones

@app.post("/token", tags=["Seguridad"])
async def login_para_obtener_token(form_data: OAuth2PasswordRequestForm = Depends()):
    # Por ahora, acepta cualquier credencial (para pruebas)
    # O solo acepta admin/admin
    if form_data.username == "admin" and form_data.password == "admin":
        return {
            "access_token": crear_token_acceso({"sub": form_data.username}),
            "token_type": "bearer"
        }
    raise HTTPException(status_code=401, detail="Credenciales incorrectas")


@app.delete("/estaciones/{id}", tags=["Gestión de Infraestructura"])
def eliminar_estacion(
    id: int,
    db: Session = Depends(get_db),
    usuario: str = Depends(obtener_identidad_actual)
):
    estacion = db.query(models.EstacionDB).filter(models.EstacionDB.id == id).first()
    if not estacion:
        raise HTTPException(status_code=404, detail="Estación no encontrada")
    
    db.query(models.LecturaDB).filter(models.LecturaDB.estacion_id == id).delete()
    db.delete(estacion)
    db.commit()
    return {"message": "Estación eliminada"}

@app.put("/estaciones/{id}", tags=["Gestión de Infraestructura"])
def actualizar_estacion(
    id: int,
    estacion_data: schemas.EstacionCreate,
    db: Session = Depends(get_db),
    usuario: str = Depends(obtener_identidad_actual)
):
    estacion = db.query(models.EstacionDB).filter(models.EstacionDB.id == id).first()
    if not estacion:
        raise HTTPException(status_code=404, detail="Estación no encontrada")
    
    estacion.nombre = estacion_data.nombre
    estacion.ubicacion = estacion_data.ubicacion
    db.commit()
    db.refresh(estacion)
    return {"message": "Estación actualizada", "data": estacion}

@app.get("/estaciones/{id}/lecturas", tags=["Telemetría de Sensores"])
def obtener_lecturas_estacion(
    id: int,
    db: Session = Depends(get_db),
    usuario: str = Depends(obtener_identidad_actual)
):
    estacion = db.query(models.EstacionDB).filter(models.EstacionDB.id == id).first()
    if not estacion:
        raise HTTPException(status_code=404, detail="Estación no encontrada")
    
    lecturas = db.query(models.LecturaDB).filter(models.LecturaDB.estacion_id == id).all()
    return [{"id": l.id, "valor": l.valor} for l in lecturas]