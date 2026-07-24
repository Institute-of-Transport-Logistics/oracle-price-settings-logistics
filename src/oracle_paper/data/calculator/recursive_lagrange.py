from bilevelpy.core.columns import DataCol
from bilevelpy.data.core import MultiEntityDataset
from oracle_paper.core.columns import BilevelDataCol
from oracle_paper.data.calculator.base import TrackableProcessor, track_metric



class RecursiveLagrangeCalculator(TrackableProcessor):
    r"""Compute recursive Lagrange multipliers for the PC-HLP model.

    Groups clients on the same route $(i,j)$ that have already been
    sorted by
    [`LinearClientRanker`][oracle_paper.data.processor.client_ranker.LinearClientRanker],
    then merges adjacent client segments where the Lagrange-to-weight
    ratio is non-increasing. The merged groups form aggregated clients
    indexed by $(i,j,z)$ where $z$ is now a group index.

    Adds four entities to the dataset:

    - [`RECURSIVE_LAGRANGE`][oracle_paper.core.columns.BilevelDataCol]
    - [`CLIENT_KEYS`][oracle_paper.core.columns.BilevelDataCol]
    - [`SUMMED_LINEAR_WEIGHTS`][oracle_paper.core.columns.BilevelDataCol]
    - [`SUMMED_BUDGETS`][oracle_paper.core.columns.BilevelDataCol]
    """

    @track_metric("recursive_lagrange_time")
    def process(self, dataset: MultiEntityDataset) -> None:
        """Compute recursive Lagrange multipliers.

        Args:
            dataset: Dataset with Lagrange multipliers, weights, budgets,
                and client keys (modified in-place).

        Raises:
            AttributeError: If required entities are missing.
        """
        if BilevelDataCol.TRANSPORT_WEIGHT_CLIENT not in dataset:
            raise AttributeError(f"{BilevelDataCol.TRANSPORT_WEIGHT_CLIENT.value}"
                                 f" not found in dataset.")

        if BilevelDataCol.LAGRANGE not in dataset:
            raise AttributeError(f"{BilevelDataCol.LAGRANGE.value}"
                                 f" not found in dataset.")

        nodes = list(dataset[DataCol.NODE_ID].values)

        lagrange = dataset[BilevelDataCol.LAGRANGE]
        weights = dataset[BilevelDataCol.TRANSPORT_WEIGHT_CLIENT]
        budget = dataset[BilevelDataCol.BUDGET]
        client_keys = dataset[BilevelDataCol.CLIENT_KEY]


        lagrange_map = {}
        keys_map = {}

        summed_weights_map = {}
        summed_budgets_map = {}
        for i in nodes:
            for j in nodes:
                if i != j:
                    dict_a = {z: a for (_,__,z), a
                              in weights(i,j).items()}
                    dict_lagrange = {z: l for (_,__,z), l
                              in lagrange(i,j).items()}
                    dict_keys = {z: key for (key,), (cur_i,cur_j,z) in client_keys.items() if i== cur_i and j== cur_j}

                    new_lagrange, new_indices = self.sort_lagrange_multipliers_dict(dict_lagrange, dict_keys, dict_a)


                    lagrange_record = {(i,j,z): new_lagrange[z] for z in new_lagrange.keys()}
                    keys_record = {(i,j,z) : new_indices[z] for z in new_indices.keys()}


                    lagrange_map.update(lagrange_record)
                    keys_map.update(keys_record)

        for (i,j,z), keys  in keys_map.items():
            summed_a = 0.0
            summed_b = 0.0
            for key in keys:
                original_i, original_j, original_z = client_keys[key]
                summed_a += weights[original_i, original_j, original_z]
                summed_b += budget[original_i, original_j, original_z]


            summed_weights_map[(i,j,z)] = summed_a
            summed_budgets_map[(i,j,z)] = summed_b


        dataset.add_entity(name=BilevelDataCol.RECURSIVE_LAGRANGE,
                           keys=[DataCol.START_NODE,
                                 DataCol.END_NODE,
                                 BilevelDataCol.CLIENT_ID_ROUTE],
                           data_map=lagrange_map
                           )

        dataset.add_entity(name=BilevelDataCol.CLIENT_KEYS,
                           keys=[DataCol.START_NODE,
                                 DataCol.END_NODE,
                                 BilevelDataCol.CLIENT_ID_ROUTE],
                           data_map=keys_map)

        dataset.add_entity(name=BilevelDataCol.SUMMED_LINEAR_WEIGHTS,
                           keys=[DataCol.START_NODE,
                                 DataCol.END_NODE,
                                 BilevelDataCol.CLIENT_ID_ROUTE],
                           data_map=summed_weights_map)

        dataset.add_entity(name=BilevelDataCol.SUMMED_BUDGETS,
                           keys=[DataCol.START_NODE,
                                 DataCol.END_NODE,
                                 BilevelDataCol.CLIENT_ID_ROUTE],
                           data_map=summed_budgets_map)

    @staticmethod
    def sort_lagrange_multipliers_dict(
        dict_lagrange: dict[int, float],
        dict_keys: dict[int, int],
        dict_a: dict[int, float],
    ) -> tuple[dict[int, float], dict[int, list[int]]]:
        r"""Merge adjacent clients where Lagrange/weight ratio is non-increasing.

        Uses a stack-based algorithm: iterates over sorted clients and
        merges when $\lambda_k/a_k > \lambda_{k+1}/a_{k+1}$.

        Args:
            dict_lagrange: $\{z: \lambda_{ij}^z\}$.
            dict_keys: $\{z: \text{original client IDs}\}$.
            dict_a: $\{z: a_{ij}^z\}$.

        Returns:
            ``(new_lagrange, new_ids)`` — merged Lagrange multipliers
            and grouped client ID lists.
        """


        stack =[]
        for k in range(len(dict_lagrange)):
            current_lagrange = dict_lagrange[k]
            current_a = dict_a[k]
            current_key =  [dict_keys[k]]

            current_ratio = current_lagrange / current_a

            while stack:
                prev_lagrange, prev_a, prev_key, prev_ratio = stack[-1]

                if prev_ratio >= current_ratio:
                    break

                # else: prev_ration < current_ration
                # in this case we need to merge the lagrange multipliers
                # pop the first element in the stack
                # and replace with later with stack.append((current_l, current_a, current_key, current_ration))
                current_lagrange += prev_lagrange
                current_a += prev_a
                prev_key.extend(current_key)
                current_key = prev_key

                current_ratio = current_lagrange / current_a

                stack.pop()

            stack.append((current_lagrange, current_a, current_key, current_ratio))

        if not stack:
            return {}, {}

        res_lagrange, res_a, res_key, res_ratio = zip(*stack)

        new_lagrange = {new_z: res_lagrange[new_z] for new_z
                        in range(len(res_lagrange))}

        new_ids = {new_z: res_key[new_z] for new_z
                   in range(len(res_key))}

        return new_lagrange, new_ids