from bilevelpy.data.core import EntityStore
from bilevelpy.models.vars.hlp_vars import AllocationVariable


class HubLocationMixin:
    """Provides hub and allocation intelligence for any HLP-based model.

    Reads the [`AllocationVariable`][bilevelpy.models.vars.hlp_vars.AllocationVariable]
    from the solution to determine which nodes are selected as hubs and
    how non-hub nodes are assigned to them.
    """

    @property
    def hubs(self) -> list[int]:
        """Returns list of node indices where X[i,i] == 1."""
        x_store: EntityStore = self._solution_data[AllocationVariable]
        return [i for (i, j), val in x_store.items() if i == j and val > 0.5]

    @property
    def allocations_dict(self) -> dict[int, list[int]]:
        """Maps nodes to their assigned hubs."""
        x_store: EntityStore = self._solution_data[AllocationVariable]
        alloc = {}
        for (i, j), val in x_store.items():
            if val > 0.5 and i != j:
                if i not in alloc: alloc[i] = []
                alloc[i].append(j)
        return alloc

    def _get_model_specific_summary(self) -> list[str]:
        """Combines Hubs, Decisions, and Pricing into one clean report."""
        # Start with the basic metadata and solver info
        lines = super()._get_model_specific_summary()

        lines.append(f"Optimal Hubs Found: {self.hubs}")
        lines.append(f"Allocations Mapping: {self.allocations_dict}")

        return lines
