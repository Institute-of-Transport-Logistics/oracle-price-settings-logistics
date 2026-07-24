import pytest

gurobipy = pytest.importorskip("gurobipy")

from oracle_paper.models.ps_hlp import PS_HLP
from oracle_paper.models.pc_hlp import PC_HLP
from oracle_paper.models.ppc_hlp import PPC_HLP
from oracle_paper.models.ps_bhlp import PS_BHLP
from tests.helpers import (
    create_base_bhlp_dataset,
    create_lagrange_dataset,
    create_recursive_lagrange_dataset,
)


# PS-HLP Tests
def test_ps_hlp_constructs():
    data = create_base_bhlp_dataset(n_nodes=3, n_clients_per_route=2)
    model = PS_HLP(n_hubs=2, alpha=0.7, data=data)
    assert model.model is not None
    assert model.model.NumVars > 0
    assert model.model.NumConstrs > 0
    assert model.model_name.value == "PS_HLP"

@pytest.mark.parametrize("n_nodes,n_hubs,n_clients", [
    (3, 1, 2),
    (5, 2, 3),
    (4, 2, 1),
])
def test_ps_hlp_scales_with_size(n_nodes, n_hubs, n_clients):
    data = create_base_bhlp_dataset(n_nodes=n_nodes, n_clients_per_route=n_clients)
    model = PS_HLP(n_hubs=n_hubs, alpha=0.5, data=data)
    assert model.model.NumVars >= n_nodes * n_nodes
    assert model.model.NumConstrs >= n_nodes


# PC-HLP Tests
def test_pc_hlp_constructs():
    data = create_recursive_lagrange_dataset(n_nodes=3, n_clients_per_route=2)
    model = PC_HLP(n_hubs=2, alpha=0.7, data=data)
    assert model.model.NumVars > 0
    assert model.model.NumConstrs > 0
    assert model.model_name.value == "PC_HLP"


# PPC-HLP Tests
def test_ppc_hlp_constructs():
    data = create_lagrange_dataset(n_nodes=3, n_clients_per_route=2)
    model = PPC_HLP(n_hubs=2, alpha=0.7, data=data)
    assert model.model.NumVars > 0
    assert model.model.NumConstrs > 0
    assert model.model_name.value == "PPC_HLP"


# PS-BHLP Tests
def test_ps_bhlp_json_payload():
    """JSON payload builds without Julia"""
    data = create_base_bhlp_dataset(n_nodes=3, n_clients_per_route=2)
    model = PS_BHLP.__new__(PS_BHLP)
    model.data = data
    model._n_hubs = 2
    model._alpha = 0.7

    payload = model._build_json_payload()
    assert payload["n_hubs"] == 2
    assert payload["alpha"] == 0.7
    assert len(payload["nodes"]) == 3
    assert len(payload["triples"]) > 0



