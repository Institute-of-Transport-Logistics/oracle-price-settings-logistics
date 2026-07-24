from oracle_paper.variables.price_variable import PriceVariable


class PriceMixin:
    """Adds a pricing table to the solution summary.

    Extracts the
    [`PriceVariable`][oracle_paper.variables.price_variable.PriceVariable]
    values from the solution and formats them as a DataFrame table.
    """

    def _get_model_specific_summary(self) -> list[str]:
        """Append a formatted pricing table to the summary lines."""

        lines = super()._get_model_specific_summary()


        df = self._solution_data[PriceVariable].to_dataframe()

        lines.append("\n--- PRICING TABLE ---")
        lines.append(df.to_string(index=False, justify='center'))
        return lines

