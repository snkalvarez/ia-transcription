-- Ejecutar una vez sobre bases de datos ya existentes antes de desplegar la versión.
ALTER TABLE procesamiento_ia
    ADD COLUMN IF NOT EXISTS vigente BOOLEAN NOT NULL DEFAULT TRUE;

-- Las respuestas vigentes existentes se conservan; el repositorio se encarga de
-- desactivar las anteriores para el mismo ingreso, tipo y día desde este cambio.
CREATE INDEX IF NOT EXISTS ix_procesamiento_ia_activo_por_dia
    ON procesamiento_ia (numero_ingreso, tipo, fecha DESC)
    WHERE vigente = TRUE;
