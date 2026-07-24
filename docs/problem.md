# The Price-Setting Bilevel Hub Location Problem

This page describes the **Price-Setting Bilevel Hub Location Problem (PS-BHLP)**
as introduced in the paper. Three solution approaches are provided
in the code, see [Solution Approaches](approaches.md).

## Problem Statement

A shipment service provider (the **leader**) operates a hub network and sets
per-unit transport prices. Customers (the **follower**) book shipments only if
the price fits their individual budget. The leader maximizes profit while
anticipating the customers' price-sensitive behavior.

### The Hub Network (Leader, upper level)

The leader selects a classical single-allocation hub network. Let
$x_{ik} \in \{0,1\}$ indicate whether node $i$ is allocated to hub $k$, with
$x_{kk}=1$ meaning $k$ is opened as a hub. The feasible set is:

$$
\text{HLP}_\text{single-alloc} =
\left\{
x \in \{0,1\}^{V \times V} \;\middle|\;
\begin{aligned}
&\sum_{j \in V} x_{jj} = \kappa, \\
&\sum_{j \in V} x_{ij} = 1 \quad \forall i \in V, \\
&x_{ij} \leq x_{jj} \quad \forall i,j \in V
\end{aligned}
\right\}
$$

The leader also sets per-unit prices $p_{ij} \geq 0$ for each origin–destination
pair $(i,j) \in V \times V$.

The cost of transporting one unit from $i$ to $j$ through the hub network is:

$$
\tilde{c}_{ij}(x) =
\sum_{k \in V} c_{ik} x_{ik}
+ \alpha \sum_{k,l \in V} c_{kl} x_{ik} x_{jl}
+ \sum_{l \in V} c_{lj} x_{jl}
$$

where $c_{ij}$ are the base transport costs and $\alpha \in [0,1]$ is the
inter-hub discount factor.

### The Customers (Follower, lower level)

For each pair $(i,j)$ there is a set of customers $\Gamma_{ij} = \{1, \dots, m_{ij}\}$.
Customer $z \in \Gamma_{ij}$ has:

- Shipment volume $a_{ij}^z > 0$
- Budget $b_{ij}^z \geq 0$

The customer books the shipment ($y_{ij}^z = 1$) iff they can afford it:
$a_{ij}^z \, p_{ij} \leq b_{ij}^z$. Customers cannot ship partial volumes.

The follower's problem therefore decomposes per route and has a trivial solution:

**Proposition 1.** *For fixed prices $p_{ij} \geq 0$, the follower's problem (FP)
has a unique optimal solution:*

$$
(y^*)_{ij}^z =
\begin{cases}
1 & \text{if } p_{ij} \leq b_{ij}^z / a_{ij}^z \\
0 & \text{otherwise}
\end{cases}
\qquad
\forall i,j \in V,\; z \in \Gamma_{ij}
$$

### Customer Sorting Assumption

Without loss of generality, customers on each route are sorted by decreasing
budget-to-volume ratio:

$$
\frac{b_{ij}^1}{a_{ij}^1} > \frac{b_{ij}^2}{a_{ij}^2} > \dots > \frac{b_{ij}^{m_{ij}}}{a_{ij}^{m_{ij}}}
\qquad \forall i,j \in V
$$

This ordering is used by the precedence constraints in the PPC-HLP approach
and is critical for the Lagrangian decomposition.

## Full Bilevel Formulation (PS-BHLP)

$$
\begin{aligned}
\max_{x,p} \quad & \sum_{i,j \in V} \sum_{z \in \Gamma_{ij}}
a_{ij}^z \, y_{ij}^z \bigl(p_{ij} - \tilde{c}_{ij}(x)\bigr) \\[4pt]
\text{s.t.} \quad & x \in \text{HLP}_\text{single-alloc} \\
& p_{ij} \geq 0 \quad \forall i,j \in V \\[4pt]
& y \in \arg\max_{y} \left\{
\sum_{i,j \in V} \sum_{z \in \Gamma_{ij}} y_{ij}^z
\;\middle|\;
\begin{aligned}
&a_{ij}^z \, p_{ij} \, y_{ij}^z \leq b_{ij}^z
\quad \forall i,j \in V, z \in \Gamma_{ij} \\[2pt]
&y_{ij}^z \in \{0,1\} \quad \forall i,j \in V, z \in \Gamma_{ij}
\end{aligned}
\right\}
\end{aligned}
$$

The leader's objective is total revenue minus transport costs. The follower
(inner problem) maximizes the number of served customers subject to budget
constraints.
