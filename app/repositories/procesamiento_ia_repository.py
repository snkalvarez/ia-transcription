from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.procesamiento_ia import ProcesamientoIA


class ProcessingRepository:

    async def get_current_active(
        self,
        db: AsyncSession,
        numero_ingreso: str,
        tipo: str,
    ) -> ProcesamientoIA | None:
        """Obtiene la respuesta vigente para el ingreso, tipo y día actuales."""
        statement = (
            select(ProcesamientoIA)
            .where(
                ProcesamientoIA.numero_ingreso == numero_ingreso,
                ProcesamientoIA.tipo == tipo,
                ProcesamientoIA.vigente.is_(True),
                func.date(ProcesamientoIA.fecha) == func.current_date(),
            )
            .order_by(ProcesamientoIA.fecha.desc())
            .limit(1)
        )
        return (await db.execute(statement)).scalar_one_or_none()

    async def save(
        self,
        db: AsyncSession,
        numero_ingreso: str,
        tipo: str,
        schema: str | None,
        resultado: dict,
    ) -> ProcesamientoIA:
        """Guarda la nueva respuesta y desactiva las del mismo grupo diario.

        El grupo está definido por número de ingreso, tipo y día de creación.
        El cambio se confirma como una sola transacción.
        """
        await db.execute(
            update(ProcesamientoIA)
            .where(
                ProcesamientoIA.numero_ingreso == numero_ingreso,
                ProcesamientoIA.tipo == tipo,
                func.date(ProcesamientoIA.fecha) == func.current_date(),
                ProcesamientoIA.vigente.is_(True),
            )
            .values(vigente=False)
        )
        procesamiento = ProcesamientoIA(
            numero_ingreso=numero_ingreso,
            tipo=tipo,
            schema=schema,
            resultado=resultado,
            vigente=True,
        )
        db.add(procesamiento)
        await db.commit()
        await db.refresh(procesamiento)

        return procesamiento
