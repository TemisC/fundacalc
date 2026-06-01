"""
Clase base abstracta para todas las normas de diseño.
Cada norma debe implementar estos métodos.
"""

from abc import ABC, abstractmethod


class NormaBase(ABC):
    """Interfaz común para todas las normas de diseño de hormigón."""

    nombre: str = "Base"
    pais: str = "N/A"
    year: int = 0
    phi_flexion: float = 0.90
    phi_cortante: float = 0.75
    seccion_as_min: str = ""   # sección de la norma que rige As_mín

    @abstractmethod
    def resistencia_punzonado(
        self, fck: float, b0: float, d: float, c1: float, c2: float
    ) -> float:
        """
        Resistencia de diseño por punzonado (cortante bidireccional).

        Args:
            fck: Resistencia característica del hormigón [MPa]
            b0:  Perímetro crítico [m]
            d:   Peralte efectivo [m]
            c1:  Dimensión columna en dirección 1 [m]
            c2:  Dimensión columna en dirección 2 [m]

        Returns:
            φ·Vn [kN]
        """
        ...

    @abstractmethod
    def resistencia_cortante_unidireccional(
        self, fck: float, bw: float, d: float
    ) -> float:
        """
        Resistencia de diseño por cortante unidireccional.

        Args:
            fck: Resistencia característica del hormigón [MPa]
            bw:  Ancho de la sección [m]
            d:   Peralte efectivo [m]

        Returns:
            φ·Vn [kN]
        """
        ...

    @abstractmethod
    def area_acero_flexion(
        self, Mu: float, d: float, fck: float, fy: float
    ) -> float:
        """
        Área de acero requerida por flexión.

        Args:
            Mu:  Momento último [kN·m/m]
            d:   Peralte efectivo [m]
            fck: Resistencia hormigón [MPa]
            fy:  Límite de fluencia del acero [MPa]

        Returns:
            As [cm²/m]
        """
        ...

    @abstractmethod
    def area_acero_minimo(
        self, fck: float, fy: float, bw: float, d: float
    ) -> float:
        """
        Área mínima de acero según la norma.

        Returns:
            As_min [cm²/m]
        """
        ...

    @abstractmethod
    def longitud_desarrollo(
        self, db: float, fck: float, fy: float
    ) -> float:
        """
        Longitud de desarrollo de barras en tracción.

        Args:
            db:  Diámetro nominal de la barra [m]
            fck: Resistencia del hormigón [MPa]
            fy:  Fluencia del acero [MPa]

        Returns:
            ld [m]
        """
        ...

    def combinaciones_carga(self) -> dict:
        """
        Factores de combinación de carga.
        Puede sobreescribirse si la norma difiere de ACI.
        """
        return {
            "principal": {"D": 1.2, "L": 1.6},
            "con_viento": {"D": 1.2, "L": 1.0, "W": 1.6},
            "con_sismo": {"D": 1.2, "L": 1.0, "E": 1.0},
        }

    def rige_label(self, As_req: float, As_min: float) -> str:
        """Devuelve etiqueta indicando qué rige el acero de diseño."""
        if As_req >= As_min - 1e-9:
            return "rige flexión"
        sec = f" {self.seccion_as_min}" if self.seccion_as_min else ""
        return f"rige As_mín ({self.nombre}{sec})"

    def __str__(self):
        return f"{self.nombre} ({self.pais}, {self.year})"
