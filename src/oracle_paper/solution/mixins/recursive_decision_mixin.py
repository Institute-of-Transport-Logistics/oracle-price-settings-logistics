from oracle_paper.core.columns import BilevelDataCol
from oracle_paper.variables.decision_variable import ClientDecisionVariable
from oracle_paper.variables.recursive_decision_variable import RecursiveClientDecisionVariable


class RecursiveDecisionMixin:
    """Handles unrolling aggregated client decisions from recursive models
    (PC-HLP) back to the original dataset indices.

    The PC-HLP model groups clients into merged segments, so Gurobi
    returns decisions for aggregated client keys. This mixin maps those
    decisions back to the original per-client indices so the solution
    summary shows individual client-level results.
    """

    def _register_custom_entities(self):
        """Unrolls aggregated client decisions back to original client indices."""
        # Call super in case other mixins also want to register things
        super()._register_custom_entities()
        self._compute_and_register_unrolled_decision()

    def _compute_and_register_unrolled_decision(self):
        """
        Maps aggregated Gurobi results back to the original client list
        using the new data pipeline architecture.
        """
        if RecursiveClientDecisionVariable not in self._dict_solution:
            raise ValueError("Recursive Decision Variable not yet registered")

        data = self._model.data
        y_dict = self._dict_solution[RecursiveClientDecisionVariable]

        # Grab our mapping dictionaries directly from the pipeline!
        client_keys = data[BilevelDataCol.CLIENT_KEYS]

        original_client_map = data[BilevelDataCol.CLIENT_KEY]


        unrolled_data = {}


        for (i, j, merged_z), decision_val in y_dict.items():

            recursive_keys = client_keys[i,j,merged_z]

            for key in recursive_keys:
                orig_i, orig_j, orig_z = original_client_map[key]
                unrolled_data[(orig_i, orig_j, orig_z)] = decision_val

        self._solution_data.add_entity(
            name=ClientDecisionVariable.var_metadata,
            keys=ClientDecisionVariable.var_metadata.identifiers,
            data_map=unrolled_data
        )

        self._dict_solution[ClientDecisionVariable.var_metadata] = unrolled_data
