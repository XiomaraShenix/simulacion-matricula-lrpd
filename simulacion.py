from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import numpy as np
import pandas as pd
import simpy


@dataclass(frozen=True)
class ConfiguracionEscenario:
    nombre: str
    estudiantes: int = 200
    media_llegadas: float = 0.35

    cap_validacion: int = 2
    cap_seleccion: int = 3
    cap_verificacion: int = 2
    cap_confirmacion: int = 2

    t_validacion: float = 1.50
    t_seleccion: float = 2.50
    t_verificacion: float = 1.00
    t_confirmacion: float = 0.80

    vacantes: int = 170
    prob_usuario_valido: float = 0.96
    prob_carrito_valido: float = 0.93
    semilla: int = 42


@dataclass
class ResultadoEscenario:
    configuracion: dict[str, Any]
    resumen: pd.DataFrame
    etapas: pd.DataFrame
    detalle: pd.DataFrame
    eventos: list[str]


class SimuladorMatricula:
    """
    Modelo académico de simulación de eventos discretos.

    El flujo agrupa los pasos públicos del proceso de matrícula en Campus
    Solutions en cuatro etapas principales:
    1. Validación académica y de condiciones.
    2. Selección de cursos y secciones.
    3. Validación del carrito, restricciones y vacantes.
    4. Inscripción y confirmación.
    """

    ETAPA_VALIDACION = "Validación académica"
    ETAPA_SELECCION = "Selección de cursos y secciones"
    ETAPA_CARRITO = "Validación del carrito"
    ETAPA_CONFIRMACION = "Inscripción y confirmación"

    def __init__(self, configuracion: ConfiguracionEscenario):
        self.c = configuracion
        self.rng = np.random.default_rng(configuracion.semilla)
        self.env = simpy.Environment()

        self.recursos = {
            self.ETAPA_VALIDACION: simpy.Resource(
                self.env, capacity=configuracion.cap_validacion
            ),
            self.ETAPA_SELECCION: simpy.Resource(
                self.env, capacity=configuracion.cap_seleccion
            ),
            self.ETAPA_CARRITO: simpy.Resource(
                self.env, capacity=configuracion.cap_verificacion
            ),
            self.ETAPA_CONFIRMACION: simpy.Resource(
                self.env, capacity=configuracion.cap_confirmacion
            ),
        }

        self.capacidades = {
            self.ETAPA_VALIDACION: configuracion.cap_validacion,
            self.ETAPA_SELECCION: configuracion.cap_seleccion,
            self.ETAPA_CARRITO: configuracion.cap_verificacion,
            self.ETAPA_CONFIRMACION: configuracion.cap_confirmacion,
        }

        self.tiempos_promedio = {
            self.ETAPA_VALIDACION: configuracion.t_validacion,
            self.ETAPA_SELECCION: configuracion.t_seleccion,
            self.ETAPA_CARRITO: configuracion.t_verificacion,
            self.ETAPA_CONFIRMACION: configuracion.t_confirmacion,
        }

        self.vacantes_restantes = configuracion.vacantes
        self.eventos: list[str] = []
        self.detalle: list[dict[str, Any]] = []
        self.esperas = {etapa: [] for etapa in self.recursos}
        self.tiempos_servicio = {etapa: [] for etapa in self.recursos}
        self.colas_maximas = {etapa: 0 for etapa in self.recursos}

    def registrar_evento(self, estudiante: int, mensaje: str) -> None:
        self.eventos.append(
            f"[{self.env.now:8.2f}] Estudiante {estudiante:03d}: {mensaje}"
        )

    def generar_tiempo_servicio(self, promedio: float) -> float:
        minimo = promedio * 0.70
        maximo = promedio * 1.30
        return float(self.rng.triangular(minimo, promedio, maximo))

    def atender_etapa(self, estudiante: int, etapa: str):
        recurso = self.recursos[etapa]
        llegada_cola = self.env.now

        self.colas_maximas[etapa] = max(
            self.colas_maximas[etapa],
            len(recurso.queue) + 1,
        )
        self.registrar_evento(estudiante, f"espera en {etapa.lower()}")

        with recurso.request() as solicitud:
            yield solicitud

            espera = self.env.now - llegada_cola
            self.esperas[etapa].append(espera)

            self.registrar_evento(
                estudiante,
                f"inicia {etapa.lower()} (espera: {espera:.2f} min)",
            )

            servicio = self.generar_tiempo_servicio(
                self.tiempos_promedio[etapa]
            )
            self.tiempos_servicio[etapa].append(servicio)

            yield self.env.timeout(servicio)
            self.registrar_evento(estudiante, f"finaliza {etapa.lower()}")

    def finalizar(self, estudiante: int, llegada: float, estado: str) -> None:
        salida = self.env.now

        self.detalle.append(
            {
                "Estudiante": estudiante,
                "Estado": estado,
                "Llegada": round(llegada, 2),
                "Salida": round(salida, 2),
                "Tiempo total (min)": round(salida - llegada, 2),
            }
        )
        self.registrar_evento(estudiante, estado.lower())

    def proceso_estudiante(self, estudiante: int):
        llegada = self.env.now
        self.registrar_evento(estudiante, "ingresa al proceso de matrícula")

        # 1. Condiciones académicas, requisitos y pagos
        yield self.env.process(
            self.atender_etapa(estudiante, self.ETAPA_VALIDACION)
        )

        if float(self.rng.random()) > self.c.prob_usuario_valido:
            self.finalizar(
                estudiante,
                llegada,
                "Rechazado: requisitos o pagos pendientes",
            )
            return

        # 2. Selección de cursos, secciones, turnos y componentes
        yield self.env.process(
            self.atender_etapa(estudiante, self.ETAPA_SELECCION)
        )

        # 3. Carrito: cruces, créditos, restricciones y vacantes
        yield self.env.process(
            self.atender_etapa(estudiante, self.ETAPA_CARRITO)
        )

        if float(self.rng.random()) > self.c.prob_carrito_valido:
            self.finalizar(
                estudiante,
                llegada,
                "Rechazado: cruce o restricción académica",
            )
            return

        if self.vacantes_restantes <= 0:
            self.finalizar(
                estudiante,
                llegada,
                "Rechazado: sin vacantes",
            )
            return

        self.vacantes_restantes -= 1

        # 4. Inscripción y finalización
        yield self.env.process(
            self.atender_etapa(estudiante, self.ETAPA_CONFIRMACION)
        )

        self.registrar_evento(
            estudiante,
            "horario disponible para consulta",
        )
        self.finalizar(
            estudiante,
            llegada,
            "Matrícula completada",
        )

    def generar_llegadas(self):
        for estudiante in range(1, self.c.estudiantes + 1):
            self.env.process(self.proceso_estudiante(estudiante))

            if estudiante < self.c.estudiantes:
                intervalo = float(
                    self.rng.exponential(self.c.media_llegadas)
                )
                yield self.env.timeout(intervalo)

    def ejecutar(self) -> ResultadoEscenario:
        self.env.process(self.generar_llegadas())
        self.env.run()

        detalle = (
            pd.DataFrame(self.detalle)
            .sort_values("Estudiante")
            .reset_index(drop=True)
        )

        exitosas = int(
            (detalle["Estado"] == "Matrícula completada").sum()
        )
        rechazadas_condiciones = int(
            (
                detalle["Estado"]
                == "Rechazado: requisitos o pagos pendientes"
            ).sum()
        )
        rechazadas_carrito = int(
            (
                detalle["Estado"]
                == "Rechazado: cruce o restricción académica"
            ).sum()
        )
        rechazadas_vacantes = int(
            (detalle["Estado"] == "Rechazado: sin vacantes").sum()
        )
        rechazadas = (
            rechazadas_condiciones
            + rechazadas_carrito
            + rechazadas_vacantes
        )

        total_esperas = sum(
            sum(valores) for valores in self.esperas.values()
        )
        cantidad_esperas = sum(
            len(valores) for valores in self.esperas.values()
        )
        espera_promedio = total_esperas / max(cantidad_esperas, 1)

        cola_mayor = max(self.colas_maximas.values())

        if cola_mayor <= 3:
            congestion = "Baja"
        elif cola_mayor <= 10:
            congestion = "Media"
        else:
            congestion = "Alta"

        duracion = float(self.env.now)
        filas_etapas = []

        for etapa in self.recursos:
            espera_etapa = self.esperas[etapa]
            servicio_etapa = self.tiempos_servicio[etapa]

            utilizacion = (
                sum(servicio_etapa)
                / max(self.capacidades[etapa] * duracion, 1e-9)
                * 100
            )

            filas_etapas.append(
                {
                    "Escenario": self.c.nombre,
                    "Etapa": etapa,
                    "Capacidad": self.capacidades[etapa],
                    "Atenciones": len(servicio_etapa),
                    "Espera promedio (min)": round(
                        sum(espera_etapa)
                        / max(len(espera_etapa), 1),
                        2,
                    ),
                    "Servicio promedio (min)": round(
                        sum(servicio_etapa)
                        / max(len(servicio_etapa), 1),
                        2,
                    ),
                    "Cola máxima": self.colas_maximas[etapa],
                    "Utilización estimada (%)": round(
                        min(utilizacion, 100.0),
                        2,
                    ),
                }
            )

        etapas = pd.DataFrame(filas_etapas)

        resumen = pd.DataFrame(
            [
                {
                    "Escenario": self.c.nombre,
                    "Estudiantes": self.c.estudiantes,
                    "Vacantes iniciales": self.c.vacantes,
                    "Matrículas exitosas": exitosas,
                    "Solicitudes rechazadas": rechazadas,
                    "Rechazos por condiciones": rechazadas_condiciones,
                    "Rechazos por validación": rechazadas_carrito,
                    "Rechazos por vacantes": rechazadas_vacantes,
                    "Tasa de éxito (%)": round(
                        exitosas
                        / max(self.c.estudiantes, 1)
                        * 100,
                        2,
                    ),
                    "Tiempo promedio total (min)": round(
                        float(detalle["Tiempo total (min)"].mean()),
                        2,
                    ),
                    "Espera promedio (min)": round(
                        espera_promedio,
                        2,
                    ),
                    "Cola máxima": cola_mayor,
                    "Congestión": congestion,
                    "Duración simulada (min)": round(
                        duracion,
                        2,
                    ),
                }
            ]
        )

        return ResultadoEscenario(
            configuracion=asdict(self.c),
            resumen=resumen,
            etapas=etapas,
            detalle=detalle,
            eventos=self.eventos,
        )


def comparar_escenarios(
    actual: ConfiguracionEscenario,
    mejorado: ConfiguracionEscenario,
) -> dict[str, ResultadoEscenario]:
    return {
        "actual": SimuladorMatricula(actual).ejecutar(),
        "mejorado": SimuladorMatricula(mejorado).ejecutar(),
    }


def construir_comparacion(
    resultados: dict[str, ResultadoEscenario],
) -> pd.DataFrame:
    return pd.concat(
        [
            resultados["actual"].resumen,
            resultados["mejorado"].resumen,
        ],
        ignore_index=True,
    )
