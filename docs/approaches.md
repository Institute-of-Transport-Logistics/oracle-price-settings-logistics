# Solution Approaches

Three solution approaches are implemented for the same [PS-BHLP problem](problem.md).
They differ in how the bilevel structure is handled, with significant
performance implications.

| Approach | Code | Method                                                                                   | Performance |
|----------|------|------------------------------------------------------------------------------------------|-------------|
| **PS-HLP** | [`PS_HLP`](reference/src/oracle_paper/models/ps_hlp.md) | Single-level Big-M reformulation (Section 2)                                             | Slowest |
| **PPC-HLP** | [`PPC_HLP`](reference/src/oracle_paper/models/ppc_hlp.md) | Lagrangian decomposition with precedence constraints (Section 3)                         | Faster |
| **PC-HLP** | [`PC_HLP`](reference/src/oracle_paper/models/pc_hlp.md) | Lagrangian decomposition with merged customers with no precedence constraints (Section 3) | **Fastest** |

All three solve the same problem and produce identical optimal values. The Lagrangian-based approaches (PPC-HLP
and PC-HLP) are the paper's main contribution.

---

## Approach 1: PS-HLP — Single-Level Big-M Reformulation

**Reference:** Theorem 7 (Section 5.1)

The classical bilevel-to-single-level approach. The follower's optimality
conditions are encoded as Big-M constraints, producing a single MIP:

$$
\begin{aligned}
\max_{x,p,y} \quad & \sum_{i,j \in V} \sum_{z \in \Gamma_{ij}}
a_{ij}^z \, y_{ij}^z \bigl(p_{ij} - \tilde{c}_{ij}(x)\bigr) \\[4pt]
\text{s.t.} \quad & x \in \text{HLP}_\text{single-alloc} \\
& 0 \leq p_{ij} \leq P \quad \forall i,j \in V \\
& a_{ij}^z \, p_{ij} - b_{ij}^z \leq M(1 - y_{ij}^z)
\quad \forall i,j \in V, z \in \Gamma_{ij} \\
& y_{ij}^z \in \{0,1\} \quad \forall i,j \in V, z \in \Gamma_{ij}
\end{aligned}
$$

where the Big-M constants are:

$$
P := \max_{i,j} \frac{b_{ij}^1}{a_{ij}^1} + 1, \qquad
M := \max_{i,j,z} a_{ij}^z \cdot P - \min_{i,j,z} b_{ij}^z
$$


### Code structure



- **Variables:** [`AllocationVariable`](https://institute-of-transport-logistics.github.io/bilevelpy/reference/bilevelpy/models/vars/#bilevelpy.models.vars.AllocationVariable),
  [`ClientDecisionVariable`][oracle_paper.variables.decision_variable.ClientDecisionVariable],
  [`LinearXYVariable`][oracle_paper.variables.linear_x_y_variable.LinearXYVariable],
  [`PriceVariable`][oracle_paper.variables.price_variable.PriceVariable]
- **Constraints:** Hub constraints (number, single allocation, assignment),
  [`LinearizationConstraint`][oracle_paper.constraints.linearization_constraint.LinearizationConstraint],
  [`BigMConstraint`][oracle_paper.constraints.big_m_constraint.BigMConstraint]

---

## Approach 2 & 3: Lagrangian Decomposition (PPC-HLP / PC-HLP)

### Optimal Lagrange Multipliers

The paper's breakthrough: the Lagrangian dual has a **closed-form solution**.
For each route $(i,j)$ and customer $k$, the optimal multipliers are:

$$
(\lambda^*)^k_{ij} :=
\left(\sum_{z=1}^{k} a_{ij}^z\right) \frac{b_{ij}^k}{a_{ij}^k}
- \left(\sum_{z=1}^{k-1} a_{ij}^z\right) \frac{b_{ij}^{k-1}}{a_{ij}^{k-1}}
$$

**Theorem 3.** *These multipliers solve the Lagrangian dual optimally
and leave **no duality gap**:*

$$
\text{OPT(PS-BHLP)} = L_{p,y}(\lambda^*) + L_{x,\bar{y}}(\lambda^*)
$$



Implementation: [`LagrangeCalculator`][oracle_paper.data.calculator.lagrange]

### Step 3: Removing Precedence Constraints 

[`PPC-HLP`][oracle_paper.models.ppc_hlp] still contains precedence constraints. **Lemma 3** shows how to
remove them by merging customers whose $\lambda_{ij}^z / a_{ij}^z$ ratios
violate monotonicity. This produces new multipliers $\mu^*$ and a more
compact problem **without precedence constraints**:

$$
Q_{x,\bar{y}}(\mu^*) = \max_{x \in \text{HLP}, \bar{y} \in \{0,1\}}
\sum_{i,j} \sum_{z} \bar{y}_{ij}^z \bigl(\mu_{ij}^z - a_{ij}^z \tilde{c}_{ij}(x)\bigr)
$$

This is the **[`PC-HLP`][oracle_paper.models.pc_hlp]** model, solved via the
[`RecursiveLagrangeCalculator`][oracle_paper.data.calculator.recursive_lagrange]
which implements **Lemma 3** (reduction of PPC-HLP to PC-HLP by merging customers
with non-monotonic $\lambda/a$ ratios).

### Recovering the Original Solution 

Given an optimal solution $(x^*, \bar{y}^*)$ of [`PC-HLP`][oracle_paper.models.pc_hlp] (or [`PPC-HLP`][oracle_paper.models.ppc_hlp]):

1. For each route $(i,j)$, let $k_{ij}$ be the largest index with
   $\bar{y}_{ij}^z = 1$ (the *critical index*)
2. Set $p^*_{ij} := b_{ij}^{k_{ij}} / a_{ij}^{k_{ij}}$
3. $y^* = \bar{y}^*$ is the optimal follower response

The resulting $(x^*, p^*)$ is optimal for the original PS-BHLP.

Implementation: [`InferredPricingMixin`][oracle_paper.solution.mixins.inferred_pricing_mixin]

---

## Paper-to-Code Reference

| Paper Result                    | What It Says | Code Implementation |
|---------------------------------|---|---|
| **Proposition 1** (Section 2)   | Follower's problem has a unique optimal solution: $y_{ij}^z=1 \iff p_{ij} \leq b_{ij}^z/a_{ij}^z$ | [`ClientDecisionVariable`][oracle_paper.variables.decision_variable.ClientDecisionVariable] — binary $y$ variables |
| **Definition 1** (Section 3)    | Optimal Lagrangian multipliers $\lambda^*$ in closed form | [`LagrangeCalculator`][oracle_paper.data.calculator.lagrange] — `process()` computes $\lambda_{ij}^k$ for all routes |
| **Theorem 3** (Section 3.2)     | $\lambda^*$ solves the Lagrangian dual with **no duality gap** | Proven: optimal value of PS-BHLP equals PC-HLP + CDP with $\lambda^*$ |
| **Lemma 3** (Section 3.2)       | PPC-HLP reduces to PC-HLP by merging customers with non-monotonic $\lambda/a$ ratios | [`RecursiveLagrangeCalculator`][oracle_paper.data.calculator.recursive_lagrange] — merges customers and produces $\mu^*$ |
| **Proposition 6** (Section 3.2) | $\lambda^*$ remains optimal even for relaxations of the hub location constraints | Enables branch-and-bound: relax $\text{HLP}_\text{single-alloc}$, solve, branch on $x$ |
| **Theorem 1** (Section 2)       | PS-BHLP is NP-hard (reduction from classical HLP) | All four models solve NP-hard problems — Gurobi with time limits |



## Computational Results from the Paper

The paper's benchmarks are in [`reproduce/benchmark_results/`](../reproduce/benchmark_results/).
Key findings (10 nodes, $\gamma = 5$, $\alpha \in \{0.5, 0.7\}$):

| Method | Avg time (s) | Instances solved |
|---|---|---|
| **PS-HLP** (Big-M) | 22–23 | All 10 |
| **PPC-HLP** (Lagrange) | 3.5–4.2 | All 10 |
| **PC-HLP** (Fast Lagrange) | 1.9 | All 10 |

At 20 nodes, PS-HLP solves only 7–8 instances within 1h while the oracle-based
approaches still solve all 10. PS-HLP fails entirely beyond 25 nodes.

See the reproduce folder in the repo to re-run the benchmarks.
