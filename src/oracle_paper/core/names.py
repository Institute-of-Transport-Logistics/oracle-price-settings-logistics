"""Model metadata identifiers for the Oracle Paper benchmark.

Defines a [`ModelMetaData`][bilevelpy.models.meta.ModelMetaData] entry
for each HLP variant so the benchmark runner and UI selectors can
reference them without importing the full model classes.
"""

from bilevelpy.models.meta import ModelMetaData


class OraclePaperModelNames:
    """Registry of [`ModelMetaData`][bilevelpy.models.meta.ModelMetaData]
    instances for all four models studied in the paper.

    Each attribute is a [`ModelMetaData`][bilevelpy.models.meta.ModelMetaData]
    carrying a short ``value`` (used for equality checks) and a
    ``display_name`` (shown in UIs and reports).

    Attributes:
        PS_HLP: Big-M price-setting model (price is a Gurobi variable).
        PC_HLP: Fast Lagrange model with recursive client aggregation.
        PPC_HLP: Standard Lagrange decomposition with precedence constraints.
        PS_BHLP: Bilevel formulation solved via Julia + BilevelJuMP.
    """

    PS_HLP = ModelMetaData(value="PS_HLP", display_name="Big M")
    PC_HLP = ModelMetaData(value="PC_HLP", display_name="Fast Lagrange")
    PPC_HLP = ModelMetaData(value="PPC_HLP", display_name="Lagrange")
    PS_BHLP = ModelMetaData(value="PS_BHLP", display_name="Bilevel")