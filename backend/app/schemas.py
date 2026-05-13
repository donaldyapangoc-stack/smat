from pydantic import BaseModel
from typing import Optional 

class EstacionCreate(BaseModel):
    id: Optional[int] = None
    nombre: str
    ubicacion: str

class LecturaCreate(BaseModel):
    estacion_id: int
    valor: float