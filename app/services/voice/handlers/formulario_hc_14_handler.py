from app.services.voice.handlers.base_handler import BaseVoiceHandler
from app.core.logger import logger


class FormularioHc14VoiceHandler(BaseVoiceHandler):

    name = "formulario_hc_14"

    @property
    def system_instruction(self) -> str:
        return (
            "Eres un asistente de voz clínico encargado de diligenciar "
            "el formulario HC14 mediante una conversación natural con el médico. "
            "Tu tarea es recopilar y registrar únicamente la información "
            "correspondiente a los campos definidos en la herramienta "
            "guardar_formulario_hc_14. "
            "No debes preguntar por campos que no estén incluidos en la herramienta. "
            "Adapta la conversación a los campos habilitados en cada momento. "
            "Si únicamente está habilitado el campo indicacionesMedicas, "
            "debes concentrarte exclusivamente en recopilar las indicaciones "
            "médicas y no debes preguntar por diagnósticos, evolución SOAP, "
            "escala de dolor, infección intrahospitalaria, educación en "
            "autocuidado ni otros campos que no estén habilitados. "
            "Si posteriormente se habilitan otros campos, debes recopilar "
            "también la información correspondiente a esos campos. "
            "Solicita al médico la información necesaria mediante preguntas "
            "claras, concretas y sin repetir preguntas ya respondidas. "
            "Registra únicamente información expresada explícitamente por "
            "el médico. No inventes datos, diagnósticos, códigos, decisiones "
            "clínicas ni indicaciones médicas. "
            "Si un dato no se proporciona, utiliza el valor vacío compatible "
            "con el tipo de dato definido en la herramienta, cuando corresponda. "
            "Respeta los tipos de datos y los valores permitidos por cada campo. "
            "Cuando hayas recopilado la información necesaria para completar "
            "los campos habilitados, ejecuta la herramienta "
            "guardar_formulario_hc_14 con la información estructurada. "
            "No devuelvas únicamente un resumen en la conversación. "
            "No finalices la sesión sin ejecutar la herramienta."
        )

    @property
    def tools(self) -> list:
        return [
            {
                "functionDeclarations": [
                    {
                        "name": "guardar_formulario_hc_14",
                        "description": (
                            "Guarda de forma estructurada la información del formulario HC14."
                        ),
                        "parameters": {
                            "type": "OBJECT",
                            "properties": {
                                "subjetivo": {
                                    "type": "STRING",
                                    "description": (
                                        "Síntomas narrados por el paciente."
                                    ),
                                },
                                "objetivo": {
                                    "type": "STRING",
                                    "description": (
                                        "Hallazgos clínicos medibles."
                                    ),
                                },
                                "analisis": {
                                    "type": "STRING",
                                    "description": (
                                        "Juicio clínico del médico."
                                    ),
                                },
                                "plan": {
                                    "type": "STRING",
                                    "description": (
                                        "Tratamiento a seguir."
                                    ),
                                },
                                "infeccionIntrahospitalaria": {
                                    "type": "BOOLEAN",
                                    "description": (
                                        "Indica si el paciente presenta infección intrahospitalaria. "
                                        "Debes preguntarle al médico explícitamente si la respuesta "
                                        "es sí o no. Registra true para sí y false para no. "
                                        "No debes inferir la respuesta."
                                    ),
                                },
                                "escalaDolor": {
                                    "type": "OBJECT",
                                    "description": (
                                        "Escala de dolor del paciente. Debe indicar el tipo de escala y su valor."
                                    ),
                                    "properties": {
                                        "tipo": {
                                            "type": "STRING",
                                            "description": (
                                                "Tipo de escala de dolor "
                                                "utilizada. Valores permitidos: "
                                                "adulto, pediatrico, neonatal."
                                            ),
                                        },
                                        "valor": {
                                            "type": "STRING",
                                            "description": (
                                                "Valor de la escala de dolor. "
                                                "Si tipo es adulto, debe ser un número del 1 al 10. "
                                                "Si tipo es pediatrico, debe ser uno de: 'no duele','duele un poquito','duele un poquito más','duele aún más','duele mucho','duele muchísimo'."
                                                "Si tipo es neonatal, debe ser uno de: 'calmado','menos marcado intermitente','marcado constante'."
                                            ),
                                        },
                                    },
                                    "required": [
                                        "tipo",
                                        "valor",
                                    ],
                                },
                                "educacionAutocuidado": {
                                    "type": "OBJECT",
                                    "description": (
                                        "Corresponde al registro de educación en autocuidado brindada por el Médico Tratante. "
                                        "Debes preguntar explícitamente si se realizó la educación. "
                                        "Si la respuesta es sí, solicita que explique qué educación "
                                        "se brindó. Si la respuesta es no, registra la respuesta negativa y deja la explicación vacía. "
                                        "No debes inferir ni inventar información."
                                    ),
                                    "properties": {
                                        "realizada": {
                                            "type": "BOOLEAN",
                                            "description": (
                                                "Indica si se realizó la educación en autocuidado. true para sí y false para no."
                                            ),
                                        },
                                        "explicacion": {
                                            "type": "STRING",
                                            "description": (
                                                "Descripción de la educación en autocuidado brindada por el Médico Tratante. Obligatoria si realizada "
                                                "es true. Si realizada es false, debe ser una cadena vacía."
                                            ),
                                        },
                                    },
                                    "required": [
                                        "realizada",
                                        "explicacion",
                                    ],
                                },                                
                                "diagnosticos": {
                                    "type": "ARRAY",
                                    "description": (
                                        "Denes preguntar si este diagnostico es principal, de ingreso, de egreso, de complicación y si debe resaltarse."
                                        "Debes preguntar por la clase, clasificacion y observacion, si no lo menciona explícitamente,"
                                        "para que el médico lo complete si lo desea."
                                        "Lista de diagnósticos mencionados explícitamente por el médico. "
                                        "Puede contener cero, uno o varios diagnósticos. "
                                        "Registrar únicamente la información dicha, o preguntar al médico para completar los campos faltantes. "
                                        "ni deducir datos faltantes."
                                    ),
                                    "items": {
                                        "type": "OBJECT",
                                        "properties": {
                                            "codigo": {
                                                "type": "STRING",
                                                "description": (
                                                    "Código CIE-10 únicamente si se menciona explícitamente. "
                                                    "No inventar ni deducir códigos."
                                                ),
                                            },
                                            "nombre": {
                                                "type": "STRING",
                                                "description": (
                                                    "Nombre del diagnóstico mencionado por el médico. Debe ser obligatorio si se menciona un diagnóstico."
                                                ),
                                            },
                                            "principal": {
                                                "type": "BOOLEAN",
                                                "description": (
                                                    "true únicamente si se identifica explícitamente como diagnóstico principal."
                                                ),
                                            },
                                            "resaltar": {
                                                "type": "BOOLEAN",
                                                "description": (
                                                    "true únicamente si se indica explícitamente que debe resaltarse."
                                                ),
                                            },
                                            "diagnosticoIngreso": {
                                                "type": "BOOLEAN",
                                                "description": (
                                                    "true únicamente si se identifica explícitamente como diagnóstico de ingreso."
                                                ),
                                            },
                                            "diagnosticoEgreso": {
                                                "type": "BOOLEAN",
                                                "description": (
                                                    "true únicamente si se identifica explícitamente como diagnóstico de egreso."
                                                ),
                                            },
                                            "diagnosticoComplicacion": {
                                                "type": "BOOLEAN",
                                                "description": (
                                                    "true únicamente si se identifica explícitamente como diagnóstico de complicación."
                                                ),
                                            },
                                            "tipo": {
                                                "type": "STRING",
                                                "description": (
                                                    "Tipo del diagnóstico, por ejemplo PRESUNTIVO o DEFINITIVO, únicamente cuando esté explícito."
                                                ),
                                            },
                                            "clase": {
                                                "type": "STRING",
                                                "description": (
                                                    "Clase del diagnóstico cuando esté explícitamente indicada. debe ser una de las siguientes: 'Impresión Diagnóstica', "
                                                    "'Confirmado Nuevo', 'Confirmado Repetido'"
                                                ),
                                            },
                                            "clasificacion": {
                                                "type": "STRING",
                                                "description": (
                                                    "Clasificación del diagnóstico cuando esté explícitamente indicada. Debe ser una de las siguientes: "
                                                    "'No Corresponse', 'Preoperatorio', 'Posoperatorio', 'Histopatológico'"
                                                ),
                                            },
                                            "observacion": {
                                                "type": "STRING",
                                                "description": (
                                                    "Observación asociada al diagnóstico si fue mencionada."
                                                    "Debes mensionarsela al médico para que la complete si lo desea, aunque no se haya mencionado explícitamente."
                                                ),
                                            },
                                        },
                                        "required":[
                                            "nombre",
                                            "tipo"
                                        ]
                                    },
                                },
                                "indicacionesMedicas": {
                                    "type": "OBJECT",
                                    "description": (
                                        "Información de las indicaciones médicas respaldadas explícitamente por la información proporcionada. "
                                        "No inventar datos ni inferir decisiones clínicas. "
                                        "Debes asegurarte de recopilar la información segun cada propiedad, y respeta el oden de las preguntas para no repetirlas. "
                                    ),
                                    "properties": {
                                        "tipo": {
                                            "type": "STRING",
                                            "description": (
                                                "Debe de indicar el tipo de indicación médica. Valores permitidos: "
                                                "'HOSPITALIZACION', 'URGENCIAS_OBSERVACION', 'CIRUGIA', 'REMISION', 'MORGUE', 'SALIDA', "
                                                "'SALIDA_CONSULTA_EXTERNA'. Seleccionar únicamente "
                                                "si está respaldado por la información proporcionada."
                                            ),
                                        },
                                        "causaExterna": {
                                            "type": "STRING",
                                            "description": (
                                                "Debe de indicar la causa externa asociada a la indicación. Valores "
                                                "permitidos: 'NINGUNA', 'ACCIDENTE_TRABAJO', "
                                                "'ACCIDENTE_HOGAR', 'ACCIDENTE_TRANSITO_ORIGEN_COMUN', "
                                                "'ACCIDENTE_TRANSITO_ORIGEN_LABORAL', "
                                                "'ACCIDENTE_ENTORNO_EDUCATIVO', 'OTRO_TIPO_ACCIDENTE', "
                                                "'EVENTO_CATASTROFICO_ORIGEN_NATURAL', 'LESION_AGRESION', "
                                                "'LESION_AUTOINFLIGIDA', 'SOSPECHA_VIOLENCIA_FISICA', "
                                                "'SOSPECHA_VIOLENCIA_PSICOLOGICA', "
                                                "'SOSPECHA_VIOLENCIA_SEXUAL', "
                                                "'SOSPECHA_NEGLIGENCIA_ABANDONO', "
                                                "'IVE_PELIGRO_SALUD_VIDA_MUJER', "
                                                "'IVE_MALFORMACION_CONGENITA_INCOMPATIBLE_VIDA', "
                                                "'IVE_VIOLENCIA_SEXUAL_INCESTO_INSEMINACION_TRANSFERENCIA_NO_CONSENTIDA', "
                                                "'EVENTO_ADVERSO_SALUD', 'ENFERMEDAD_GENERAL', "
                                                "'ENFERMEDAD_LABORAL', "
                                                "'ATENCION_POBLACION_MATERNO_PERINATAL', "
                                                "'RIESGO_AMBIENTAL', 'OTROS_EVENTOS_CATASTROFICOS', "
                                                "'ACCIDENTE_MINA_ANTIPERSONAL_MAP', "
                                                "'ACCIDENTE_ARTEFACTO_EXPLOSIVO_IMPROVISADO_AEI', "
                                                "'ACCIDENTE_MUNICION_SIN_EXPLOTAR_MUSE', "
                                                "'OTRA_VICTIMA_CONFLICTO_ARMADO_COLOMBIANO', "
                                                "'IVE_DECISION_VOLUNTAD_PERSONA_GESTANTE_HASTA_SEMANA_24'. "
                                                "Usar 'NINGUNA' solamente "
                                                "si se indica explícitamente que no existe causa externa."
                                            ),
                                        },
                                        "finalidadConsulta": {
                                            "type": "STRING",
                                            "description": (
                                                "Debe de indicar la finalidad de la consulta. Valores permitidos: "
                                                "'NINGUNA', 'VALORACION_INTEGRAL_PROMOCION_MANTENIMIENTO', "
                                                "'DETECCION_TEMPRANA_ENFERMEDAD_GENERAL', "
                                                "'DETECCION_TEMPRANA_ENFERMEDAD_LABORAL', 'DIAGNOSTICO', "
                                                "'TRATAMIENTO', 'REHABILITACION', 'PALIACION', "
                                                "'PLANIFICACION_FAMILIAR_ANTICONCEPCION', "
                                                "'PROMOCION_APOYO_LACTANCIA_MATERNA', "
                                                "'ATENCION_BASICA_ORIENTACION_FAMILIAR', "
                                                "'ATENCION_CUIDADO_PRECONCEPCIONAL', "
                                                "'ATENCION_CUIDADO_PRENATAL', "
                                                "'INTERRUPCION_VOLUNTARIA_EMBARAZO', "
                                                "'ATENCION_PARTO_PUERPERIO', 'SEGUIMIENTO_RECIEN_NACIDO', "
                                                "'MODIFICACION_ESTETICA_CORPORAL'. "
                                                "Seleccionar solo cuando exista respaldo explícito; "
                                                "si no puede determinarse, usar 'DIAGNOSTICO'."
                                            ),
                                        },
                                        "trasladarPaciente": {
                                            "type": "OBJECT",
                                            "description": (
                                                "Debe solicitar únicamente cuando el tipo de indicación médica es 'HOSPITALIZACION' o 'URGENCIAS_OBSERVACION'. "
                                                "Cuando corresponda a uno de estos tipos, pregunta explícitamente "
                                                "al médico si se debe trasladar al paciente, incluso si no ha "
                                                "mencionado un traslado. No infieras que no habrá traslado por "
                                                "el simple hecho de que no se mencione. "
                                                "Si el tipo de indicación es diferente, no solicites información "
                                                "sobre el traslado y utiliza los valores vacíos correspondientes."
                                            ),
                                            "properties": {
                                                "realizar": {
                                                    "type": "STRING",
                                                    "description": (
                                                        "Valores permitidos: 'SI', 'NO'. "
                                                        "Cuando el tipo de indicación sea 'HOSPITALIZACION' o "
                                                        "'URGENCIAS_OBSERVACION', pregunta explícitamente si se "
                                                        "debe trasladar al paciente. Usa 'SI' si el médico confirma "
                                                        "el traslado y 'NO' si confirma que no se realizará. "
                                                    ),
                                                },
                                                "condiciones": {
                                                    "type": "STRING",
                                                    "description": (
                                                        "Condiciones necesarias para realizar el traslado. "
                                                        "Si 'realizar' es 'SI', pregunta al médico cuáles son "
                                                        "las condiciones del traslado si aún no las ha mencionado. "
                                                    ),
                                                },
                                                "motivo": {
                                                    "type": "STRING",
                                                    "description": (
                                                        "Motivo por el cual se realizará el traslado. "
                                                        "Si 'realizar' es 'SI', pregunta al médico el motivo "
                                                        "si aún no lo ha mencionado. "
                                                        "No inventes motivos."
                                                    ),
                                                },
                                                "aislamiento": {
                                                    "type": "STRING",
                                                    "description": (
                                                        "Tipo de aislamiento indicado. Valores permitidos: "
                                                        "'PRECAUCION_ESTANDAR', 'TRANSMISION_VIA_AEREA', "
                                                        "'PRECAUCION_GOTAS', 'PRECAUCION_CONTACTO', "
                                                        "'AISLAMIENTO_COHORTE', 'AMBIENTE_PROTEGIDO', "
                                                        "'AISLAMIENTO_VECTORES', 'NINGUNO'. "
                                                        "Aplica para hospitalización y urgencias observación. "
                                                        "Usar 'NINGUNO' solo "
                                                        "si se indica explícitamente."
                                                    ),
                                                },
                                            },
                                            "required": [
                                                "realizar",
                                                "condiciones",
                                                "motivo",
                                                "aislamiento",  
                                            ],
                                        },
                                        "condicionDestino": {
                                            "type": "STRING",
                                            "description": (
                                                "Debe llenarse unicamente cuando el tipo de indicación medica es 'SALIDA', 'SALIDA_CONSULTA_EXTERNA'. "
                                                "Condición y destino del paciente. Valores permitidos: "
                                                "'NINGUNA', 'PACIENTE_DESTINO_DOMICILIO', "
                                                "'PACIENTE_MUERTO', 'REFERIDO_OTRA_INSTITUCION', "
                                                "'CONTRAREFERIDO_OTRA_INSTITUCION', "
                                                "'HOSPITALIZACION_DOMICILIARIA', "
                                                "'DERIVADO_SERVICIO_SOCIAL', "
                                                "'PACIENTE_CONTINUA_SERVICIO'. "
                                                "Aplica para salida y salida consulta externa. "
                                            ),
                                        },
                                        "finalizarAtencion": {
                                            "type": "BOOLEAN",
                                            "description": (
                                                "Debes preguntar para asi validar si debe finalizarse la atención, únicamente "
                                                "cuando exista respaldo explícito. Usar false si "
                                                "no se indica que deba finalizarse."
                                            ),
                                        },
                                        "detalle": {
                                            "type": "STRING",
                                            "description": (
                                                "Debes preguntar si existe detalle de la indicación médica: conducta, tratamiento, "
                                                "procedimiento, estudio, hospitalización, remisión u "
                                                "otra acción indicada. Copiar el contenido respaldado "
                                                "por la información proporcionada sin inventar datos. "
                                            ),
                                        },
                                    },
                                    "required": [
                                        "tipo",
                                        "causaExterna",
                                        "finalidadConsulta",
                                        "trasladarPaciente",
                                        "condicionDestino",
                                        "finalizarAtencion",
                                        "detalle",
                                    ],
                                },
                            
                            },
                            "required": [
                                "subjetivo",
                                "objetivo",
                                "analisis",
                                "plan",
                                "infeccionIntrahospitalaria",
                                "escalaDolor",
                                "educacionAutocuidado",
                                "diagnosticos",
                                "indicacionesMedicas"
                            ],
                        },
                    }
                ]
            }
        ]

    @property
    def ends_session_after_tool_call(self) -> bool:
        """
        HC14 finaliza automáticamente la conversación
        cuando Gemini ejecuta guardar_formulario_hc_14.
        """
        return False

    async def handle_tool_call(
        self,
        call: dict,
        sio,
        sid: str,
    ):
        """
        Procesa las herramientas propias del flujo HC14.
        """

        if call["name"] != "guardar_formulario_hc_14":
            return None

        extracted_hc14 = call["args"]

        logger.info(
            f"Formulario HC14 completo extraído "
            f"exitosamente para {sid}!"
        )

        logger.info(
            extracted_hc14
        )

        # ======================================================
        # ENVIAR RESULTADO AL FRONTEND
        # ======================================================

        await sio.emit(
            "voice_result",
            extracted_hc14,
            to=sid,
        )

        return {
            "success": True
        }
