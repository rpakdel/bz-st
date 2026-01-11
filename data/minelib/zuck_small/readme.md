
# Block model:
9400 blocks of unknown size
Blockfile columns detail:
id x y z cost value rock_tonnes ore_tonnes

# Blockvalue computation
Discount rate = 0.1
Type of Constraints:
C0 Capacity constraint (mine): Total extracted tonnage < 60M
C1 Capacity constraint (process): Total processed tonnage < 20M

# Solution files:
## UPIT
zuck_small_upit.sol
Objective value: 1,422,726,898
Computed using Hochbaum's pseudoflow algorithm.

## CPIT
zuck_small_cpit_gmunoz120723.sol
Objective value: 788,652,600 (LP GAP 7.7%)
Provided by Gonzalo Muñoz, and obtained from the LP relaxation using a modified TopoSort heuristic.

zuck_small.LPcpit
LP relaxation solution (not feasible)
Objective value: 854,182,396
Computed using a modified version of Bienstock & Zuckerberg algorithm. 

# PCPSP
zuck_small_pcpsp_gmunoz120723.sol
Objective value: 872,372,967 (LP GAP 3.7%)
Provided by Gonzalo Muñoz, and obtained from the LP relaxation using a modified TopoSort heuristic.

zuck_small.LPpcpsp
LP relaxation solution (not feasible)
Objective value: 905,878,172
Computed using a modified version of Bienstock & Zuckerberg algorithm
