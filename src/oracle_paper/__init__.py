"""Oracle Paper — reference implementation for price-setting problems in logistics.

This package provides four solution approaches for the Price-Setting
Bilevel Hub Location Problem (PS-BHLP), built on top of BilevelPy:

- [`PS_HLP`][oracle_paper.models.ps_hlp.PS_HLP] — Big-M linearization
- [`PC_HLP`][oracle_paper.models.pc_hlp.PC_HLP] — Fast Lagrange with
  recursive client aggregation
- [`PPC_HLP`][oracle_paper.models.ppc_hlp.PPC_HLP] — Standard Lagrange
  decomposition with precedence constraints
- [`PS_BHLP`][oracle_paper.models.ps_bhlp.PS_BHLP] — Bilevel formulation
  (requires Julia)
"""

from oracle_paper.core.columns import BilevelDataCol
from oracle_paper.core.names import OraclePaperModelNames
from oracle_paper.models.pc_hlp import PC_HLP
from oracle_paper.models.ppc_hlp import PPC_HLP
from oracle_paper.models.ps_hlp import PS_HLP
from oracle_paper.models.ps_bhlp import PS_BHLP

__all__ = [
    "BilevelDataCol",
    "OraclePaperModelNames",
    "PC_HLP",
    "PPC_HLP",
    "PS_HLP",
    "PS_BHLP",
]