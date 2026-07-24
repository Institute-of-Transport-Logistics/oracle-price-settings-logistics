from bilevelpy.core.columns import DataCol
from bilevelpy.data.core import MultiEntityDataset
from oracle_paper.core.columns import BilevelDataCol
from oracle_paper.data.calculator.base import TrackableProcessor, track_metric


class LagrangeCalculator(TrackableProcessor):
    r"""Compute Lagrange multipliers $\lambda_{ij}^z$ for the PPC-HLP model.

    For each route $(i,j)$, the calculator sorts clients by their
    budget-to-weight ratio and computes the Lagrange multiplier sequence
    using the recursive formula:

    $$\lambda_k = b_k + \sum_{t=0}^{k-1} a_t \cdot
    \left(\frac{b_k}{a_k} - \frac{b_{k-1}}{a_{k-1}}\right)$$

    The result is stored in
    [`BilevelDataCol.LAGRANGE`][oracle_paper.core.columns.BilevelDataCol].

    Uses the [`track_metric`][oracle_paper.data.calculator.base.track_metric]
    decorator to measure computation time automatically.
    """

    @track_metric("lagrange_time")
    def process(self, dataset: MultiEntityDataset) -> None:
        """Compute Lagrange multipliers and add them to the dataset.

        Args:
            dataset: Dataset with client weights and budgets
                (modified in-place).

        Raises:
            AttributeError: If required entities are missing.
        """

        if BilevelDataCol.TRANSPORT_WEIGHT_CLIENT not in dataset:
            raise AttributeError(f"{BilevelDataCol.TRANSPORT_WEIGHT_CLIENT.value}"
                                 f" not found in dataset.")

        if BilevelDataCol.BUDGET not in dataset:
            raise AttributeError(f"{BilevelDataCol.BUDGET.value}"
                                 f" not found in dataset.")

        nodes = list(dataset[DataCol.NODE_ID].values)

        weights = dataset[BilevelDataCol.TRANSPORT_WEIGHT_CLIENT]
        budgets = dataset[BilevelDataCol.BUDGET]

        lagrange_map = {}
        for i in nodes:
            for j in nodes:
                if i != j:
                    dict_a = {z: a for (i,j,z), a
                              in weights(i,j).items()}
                    dict_b = {z: budget for (i,j,z), budget
                              in budgets(i,j).items()}

                    lagrange = self.calculate_lagrange(dict_a, dict_b)
                    lagrange_record = {(i,j,z): lagrange[z] for z in lagrange.keys()}
                    lagrange_map.update(lagrange_record)


        dataset.add_entity(name=BilevelDataCol.LAGRANGE,
                           keys=[DataCol.START_NODE,
                                 DataCol.END_NODE,
                                 BilevelDataCol.CLIENT_ID_ROUTE],
                           data_map=lagrange_map)

    @staticmethod
    def calculate_lagrange(
        dict_a: dict[int, float], dict_b: dict[int, float]
    ) -> dict[int, float]:
        r"""Compute the Lagrange multiplier sequence for one route's clients.

        $$\lambda_k = b_k + \sum_{t=0}^{k-1} a_t \cdot \Delta_k$$
        where $\Delta_k = b_k/a_k - b_{k-1}/a_{k-1}$.

        Args:
            dict_a: Client weights $\{z: a_{ij}^z\}$ sorted by $z$.
            dict_b: Client budgets $\{z: b_{ij}^z\}$ sorted by $z$.

        Returns:
            Mapping $\{z: \lambda_{ij}^z\}$ of Lagrange multipliers.
        """
        curr_sum = 0.0
        lagrange = {}

        sorted_z = sorted(dict_a.keys())

        for k in sorted_z:
            if k == 0:
                curr_lagrange = dict_b[k]
            else:
                curr_lagrange = dict_b[k] + curr_sum * (
                        (dict_b[k] / dict_a[k]) - (dict_b[k - 1] / dict_a[k - 1])
                )
            curr_sum += dict_a[k]
            lagrange[k] = curr_lagrange
        return lagrange

