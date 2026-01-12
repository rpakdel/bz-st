# Description:
Mine provided by Alexandra Newman

# Block model:
1060 blocks of unknown size
precedence computed using 5 blocks above (+)

# Blockfile columns detail:
id x y z type grade tonns min_caf value_extracc value_proc apriori_process

# Blockvalue computation
Extraction cost = tonns * min_caf * 1
Process benefit: (19.29 * Recovery * Grade - Process_cost) * tonns
Process cost = 8.195 (if Type=OXOR), 16.862 (if Type=FRWS or FROR)
Recovery = 90% (if Type=OXOR), 84% (if Type=FRWS or FROR)
Discount rate = 0.08

# Type of Constraints:
C0 Capacity constraint (mine): Total extracted tonnage min = 1400000 max = 2000000
C1 Capacity constraint (process): Total processed tonnage min = 900000 max = 1100000

# File downloads:
.blocks file: newman1.blocks
.prec file: newman1.prec
.upit file: newman1.upit
.cpit file: newman1.cpit
.pcpsp file: newman1.pcpsp

# Solution files:
## UPIT
newman1_upit.sol
Objective value: 26,086,899
Computed using Hochbaum's pseudoflow algorithm.

## CPIT
newman1_cpit_gmunoz120723.sol
Objective value: 23,483,671 (LP GAP 4.1%)
Provided by Gonzalo Muñoz, and obtained from the LP relaxation using a modified TopoSort heuristic.

newman1.LPcpit
LP relaxation solution (not feasible)
Objective value: 24,486,184
Computed using a modified version of Bienstock & Zuckerberg algorithm.

## PCPSP
newman1_pcpsp_gmunoz120723.sol
Objective value: 23,658,230 (LP GAP 3.4%)
Provided by Gonzalo Muñoz, and obtained from the LP relaxation using a modified TopoSort heuristic.

newman1.LPpcpsp
LP relaxation solution (not feasible)
Objective value: 24,486,549
Computed using a modified version of Bienstock & Zuckerberg algorithm.
