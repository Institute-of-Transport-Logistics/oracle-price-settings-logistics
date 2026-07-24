"""Mixin that extracts and formats client decision variable values."""

from oracle_paper.variables.decision_variable import ClientDecisionVariable


class DecisionMixin:
    """Adds a decision table (active routes only) to the solution summary.

    Uses
    [`ClientDecisionVariable`][oracle_paper.variables.decision_variable.ClientDecisionVariable]
    and filters to show only routes where $y_{ij}^z > 0.5$.
    """

    def _get_model_specific_summary(self) -> list[str]:
        """Append an active-routes-only decision table."""
        # 1. Continue the chain (calls HubLocationMixin next)
        lines = super()._get_model_specific_summary()

        # 2. Safety check: does this variable even exist in this solution?
        Y = ClientDecisionVariable.var_metadata
        if ClientDecisionVariable in self._solution_data:
            df = self._solution_data[ClientDecisionVariable].to_dataframe()

            # Filter to only show active decisions (val > 0.5)
            active_df = df[df[Y] > 0.5]

            lines.append("\n--- DECISION TABLE (Active Only) ---")
            if not active_df.empty:
                lines.append(active_df.head(10).to_string(index=False, justify='center'))
                lines.append(f"... showing top 10 of {len(active_df)} active routes ...")
            else:
                lines.append("No active client decisions found.")

        return lines