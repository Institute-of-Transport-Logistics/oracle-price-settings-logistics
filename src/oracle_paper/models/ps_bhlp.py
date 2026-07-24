"""Bilevel price-setting hub location — Julia Big-M reformulation, solved by gurobipy."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import ClassVar

import gurobipy as gp
from bilevelpy import SolutionRegistry
from bilevelpy.solution.core import BaseModelSolution

from bilevelpy.data.core import MultiEntityDataset
from bilevelpy.models.core import BaseModel
from bilevelpy.models.meta import ModelMetaData
from bilevelpy.core.columns import DataCol

from oracle_paper.core.columns import BilevelDataCol
from oracle_paper.core.names import OraclePaperModelNames

# Path to the Julia script (same directory as this file)
_JULIA_SCRIPT: Path = Path(__file__).resolve().parent / "bilevel_model.jl"


from oracle_paper._julia import find_julia

_JULIA_EXE: str = find_julia() or "julia"

@SolutionRegistry.register_for(BaseModelSolution)
class PS_BHLP(BaseModel):
    """PS-BHLP solved via Julia Big-M reformulation.

    Requires Julia ≥ 1.10 with JuMP, Gurobi, BilevelJuMP, and JSON on PATH.
    """
    model_metadata = OraclePaperModelNames.PS_BHLP
    # Julia script location (class-level so it can be overridden in tests)
    julia_script: ClassVar[Path] = _JULIA_SCRIPT

    def __init__(
        self,
        n_hubs: int,
        alpha: float,
        data: MultiEntityDataset,
    ) -> None:
        super().__init__(data)
        self._n_hubs = n_hubs
        self._alpha = alpha

        json_payload = self._build_json_payload()

        lp_path: str | None = None
        json_path: str | None = None

        try:
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".json", delete=False, encoding="utf-8"
            ) as jf:
                json.dump(json_payload, jf)
                json_path = jf.name

            lp_path = json_path.replace(".json", ".lp")

            result = subprocess.run(
                [
                    _JULIA_EXE,
                    str(self.julia_script),
                    json_path,
                    lp_path,
                ],
                capture_output=True,
                text=True,
                timeout=600,
            )

            if result.returncode != 0:
                raise RuntimeError(
                    f"Julia PS_BHLP model generation failed.\n"
                    f"STDERR:\n{result.stderr}\n"
                    f"STDOUT:\n{result.stdout}"
                )

            if not os.path.exists(lp_path) or os.path.getsize(lp_path) == 0:
                raise RuntimeError(
                    f"Julia exited successfully but no LP file was produced "
                    f"at {lp_path}"
                )

            self.model = gp.read(lp_path)

        finally:
            for path in (json_path, lp_path):
                if path and os.path.exists(path):
                    try:
                        os.unlink(path)
                    except OSError:
                        pass


    def _build_json_payload(self) -> dict:
        """Build the JSON dictionary consumed by ``bilevel_model.jl``."""
        data = self.data

        nodes = list(data[DataCol.NODE_ID].values)

        client_id_store = data[BilevelDataCol.CLIENT_ID_ROUTE]
        triples = [list(k) for k in client_id_store]

        a_store = data[BilevelDataCol.TRANSPORT_WEIGHT_CLIENT]
        b_store = data[BilevelDataCol.BUDGET]

        a_dict = {}
        b_dict = {}
        for t in triples:
            key = ",".join(str(x) for x in t)
            a_dict[key] = float(a_store[tuple(t)])
            b_dict[key] = float(b_store[tuple(t)])

        cost_store = data[DataCol.COST_NODE_TO_NODE]
        costs_dict = {}
        for (i, j), val in cost_store.items():
            costs_dict[f"{i},{j}"] = float(val)

        return {
            "nodes": [int(n) for n in nodes],
            "triples": triples,
            "a": a_dict,
            "b": b_dict,
            "costs": costs_dict,
            "n_hubs": int(self._n_hubs),
            "alpha": float(self._alpha),
        }