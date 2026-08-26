import json
from pathlib import Path


class SchemaBuilderError(Exception):
    """Error al construir el schema completo para Groq."""


class SchemaBuilder:
    """
    Construye un schema JSON completo resolviendo referencias
    ($ref) a otros archivos JSON locales.
    """

    def __init__(self, schemas_dir: Path):
        self.schemas_dir = Path(schemas_dir)

    def build(self, schema_filename: str) -> dict:
        """
        Carga el schema maestro y resuelve todos los $ref externos.
        """

        root_path = self.schemas_dir / schema_filename

        if not root_path.exists():
            raise SchemaBuilderError(
                f"No existe el schema: {root_path}"
            )

        document = self._load_json(root_path)

        if "name" not in document:
            raise SchemaBuilderError(
                f"El schema {schema_filename} no contiene 'name'."
            )

        if "schema" not in document:
            raise SchemaBuilderError(
                f"El schema {schema_filename} no contiene 'schema'."
            )

        schema = self._resolve_refs(
            document["schema"],
            root_path,
            []
        )

        return {
            "name": document["name"],
            "schema": schema
        }

    def _resolve_refs(
        self,
        value,
        current_file: Path,
        resolving_stack: list[Path]
    ):
        """
        Recorre recursivamente el JSON y reemplaza los $ref
        externos por el contenido real del archivo.
        """

        if isinstance(value, dict):

            if "$ref" in value:

                ref = value["$ref"]

                # Por ahora solamente manejamos referencias
                # a archivos JSON locales.
                if ref.startswith("#"):
                    raise SchemaBuilderError(
                        f"Referencia interna no soportada: "
                        f"{ref} en {current_file}"
                    )

                referenced_file = (
                    current_file.parent / ref
                ).resolve()

                if not referenced_file.exists():
                    raise SchemaBuilderError(
                        f"No existe el archivo referenciado: "
                        f"{referenced_file}"
                    )

                # Detectar referencias circulares.
                if referenced_file in resolving_stack:
                    chain = " -> ".join(
                        str(path)
                        for path in resolving_stack + [referenced_file]
                    )

                    raise SchemaBuilderError(
                        f"Referencia circular detectada: {chain}"
                    )

                referenced_document = self._load_json(
                    referenced_file
                )

                if "schema" not in referenced_document:
                    raise SchemaBuilderError(
                        f"El archivo {referenced_file} "
                        f"no contiene la propiedad 'schema'."
                    )

                resolved = self._resolve_refs(
                    referenced_document["schema"],
                    referenced_file,
                    resolving_stack + [referenced_file]
                )

                # Si además del $ref existen otras propiedades,
                # las conservamos.
                extra_properties = {
                    key: val
                    for key, val in value.items()
                    if key != "$ref"
                }

                if extra_properties:

                    if not isinstance(resolved, dict):
                        raise SchemaBuilderError(
                            f"No se pueden combinar propiedades "
                            f"adicionales con {ref}."
                        )

                    extra_resolved = self._resolve_refs(
                        extra_properties,
                        current_file,
                        resolving_stack
                    )

                    resolved.update(extra_resolved)

                return resolved

            return {
                key: self._resolve_refs(
                    val,
                    current_file,
                    resolving_stack
                )
                for key, val in value.items()
            }

        if isinstance(value, list):
            return [
                self._resolve_refs(
                    item,
                    current_file,
                    resolving_stack
                )
                for item in value
            ]

        return value

    @staticmethod
    def _load_json(path: Path) -> dict:
        try:
            with path.open("r", encoding="utf-8") as file:
                return json.load(file)

        except json.JSONDecodeError as exc:
            raise SchemaBuilderError(
                f"JSON inválido en {path}: {exc}"
            ) from exc

        except OSError as exc:
            raise SchemaBuilderError(
                f"No fue posible leer {path}: {exc}"
            ) from exc