#!/usr/bin/env julia
#=
Standalone CLI that builds the PS-BHLP Big-M reformulation and writes it as
a flat MIP (.lp) file. Python / gurobipy solves it — Julia just generates the
formulation.

Usage:
    julia bilevel_model.jl <input.json> <output.lp>

Requires Julia ≥ 1.10, Gurobi, JuMP, and BilevelJuMP.

JSON input shape:
    {
        "nodes":         [0, 1, 2, ...],
        "triples":       [[0, 1, 0], [0, 2, 0], ...],
        "a":             {"0,1,0": 100.0, "0,2,0": 50.0, ...},
        "b":             {"0,1,0": 450.0, "0,2,0": 200.0, ...},
        "costs":         {"0,1": 45.0, "0,2": 67.0, ...},
        "n_hubs":        2,
        "alpha":         0.7
    }
=#

using JuMP
using Gurobi
using BilevelJuMP
using JSON

if length(ARGS) < 2
    println(stderr, "Usage: julia bilevel_model.jl <input.json> <output.lp>")
    exit(1)
end

input_path  = ARGS[1]
output_path = ARGS[2]

data = JSON.parsefile(input_path)

nodes        = data["nodes"]
triples_raw  = data["triples"]
triples      = [tuple(t...) for t in triples_raw]

a_raw    = data["a"]
b_raw    = data["b"]
costs_raw = data["costs"]

function parse_key(k::String)
    parts = split(k, ",")
    return tuple(parse.(Int, parts)...)
end

a     = Dict{Tuple{Int,Int,Int}, Float64}(parse_key(k) => v for (k, v) in a_raw)
b     = Dict{Tuple{Int,Int,Int}, Float64}(parse_key(k) => v for (k, v) in b_raw)
costs = Dict{Tuple{Int,Int}, Float64}(parse_key(k) => v for (k, v) in costs_raw)

n_hubs = data["n_hubs"]
alpha  = data["alpha"]

M_val = 10000.0  # Big-M constant

model = BilevelModel(Gurobi.Optimizer)

N = nodes
T = triples

# Upper-level variables
@variable(Upper(model), x[i in N, j in N], Bin)
@variable(Upper(model), X[i in N, j in N, h in N, m in N], Bin)
@variable(Upper(model), 0 <= p[i in N, j in N; i != j] <= b[i, j, 0] / a[i, j, 0] + 1)

# Lower-level variables
@variable(Lower(model), 0 <= y[t in T] <= 1)
@variable(Lower(model), z[t in T] >= 0)

# Hub location constraints (upper level)
@constraint(Upper(model), sum(x[j, j] for j in N) == n_hubs)
@constraint(Upper(model), [i in N], sum(x[i, j] for j in N) == 1)
@constraint(Upper(model), [i in N, j in N], x[i, j] <= x[j, j])

# Linearization: X[i,j,h,m] = x[i,h] * x[j,m]
@constraint(Upper(model), [i in N, j in N, h in N, m in N], X[i, j, h, m] <= x[i, h])
@constraint(Upper(model), [i in N, j in N, h in N, m in N], X[i, j, h, m] <= x[j, m])
@constraint(Upper(model), [i in N, j in N, h in N, m in N],
    X[i, j, h, m] >= x[i, h] + x[j, m] - 1)

# Lower-level constraints (Big-M reformulation)
@constraint(Lower(model), [t in T], z[t] <= p[t[1], t[2]])
@constraint(Lower(model), [t in T], a[t] * z[t] <= b[t])
@constraint(Lower(model), [t in T],
    y[t] <= M_val * (b[t] / a[t] - z[t]))

# Follower maximizes utility
@objective(Lower(model), Max, sum(y[t] + (M_val + 1) * z[t] for t in T))

# Leader maximizes profit
@objective(Upper(model), Max, begin
    expr = 0
    for t in T
        i, j = t[1], t[2]
        if i != j
            revenue = p[i, j]
            current_t_hub_costs = 0.0
            for h in N, m in N
                current_t_hub_costs += X[i, j, h, m] * (
                    costs[(i, h)] +
                    alpha * costs[(h, m)] +
                    costs[(m, j)]
                )
            end
            expr += a[t] * y[t] * (revenue - current_t_hub_costs)
        end
    end
    expr
end)

# Write the LP 
# Solving is done by the bilevelpy library 
set_optimizer_attribute(model, "TimeLimit", 0.0)
optimize!(model; solver_prob=output_path)