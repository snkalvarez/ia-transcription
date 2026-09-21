from pydantic import BaseModel


class ProcesamientoRequest(BaseModel):
    transcripcion: str
    numero_ingreso: str
    tipo: str