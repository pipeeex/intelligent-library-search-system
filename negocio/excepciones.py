"""Errores de negocio del backend.

Cada uno se traduce a un codigo de estado gRPC en la capa de servicio.
"""


class ErrorNegocio(Exception):
    """Base de los errores previsibles del dominio."""

    codigo = "ERROR_NEGOCIO"


class NoEncontrado(ErrorNegocio):
    codigo = "NO_ENCONTRADO"


class DatosInvalidos(ErrorNegocio):
    codigo = "DATOS_INVALIDOS"


class ReglaViolada(ErrorNegocio):
    """La operacion es valida sintacticamente pero rompe una regla del negocio."""

    codigo = "REGLA_VIOLADA"


class SinDisponibilidad(ReglaViolada):
    codigo = "SIN_DISPONIBILIDAD"
