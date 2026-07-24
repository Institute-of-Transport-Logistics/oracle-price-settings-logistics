"""Constraint definitions for the four PS-BHLP solution approaches.

- [`BigMConstraint`][oracle_paper.constraints.big_m_constraint.BigMConstraint] —
  couples the leader's price with the follower's decision
- [`LinearizationConstraint`][oracle_paper.constraints.linearization_constraint.LinearizationConstraint] —
  linearizes the cubic term $y \cdot x \cdot x$
- [`PrecedenceConstraint`][oracle_paper.constraints.precedence_constraint.PrecendenceConstraint] —
  enforces ordered client acceptance
- [`RecursiveLinearizationConstraint`][oracle_paper.constraints.recursive_linearization_constraint.RecursiveLinearizationConstraint] —
  aggregated-client version for PC-HLP
"""

from oracle_paper.constraints.big_m_constraint import BigMConstraint
from oracle_paper.constraints.linearization_constraint import LinearizationConstraint
from oracle_paper.constraints.precedence_constraint import PrecedenceConstraint
from oracle_paper.constraints.recursive_linearization_constraint import RecursiveLinearizationConstraint

__all__ = [
    "BigMConstraint",
    "LinearizationConstraint",
    "PrecedenceConstraint",
    "RecursiveLinearizationConstraint",
]