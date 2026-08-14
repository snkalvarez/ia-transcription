from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ProcesamientoIA(Base):
    __tablename__ = "procesamiento_ia"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    numero_ingreso: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    fecha: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    tipo: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    schema: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    resultado: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
    )

    vigente: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
        index=True,
    )
