Arizona’s Copper Deposit (KD)

# Block model:
Blocks dimension: 20x20x15 m
Precedence computed with 45 degrees using 8 levels
Destinations: 1=ore, 2=waste
Blockfile columns detail:
<id> <x> <y> <z> <tonn> <blockvalue> <destination> <CU %> <process_profit>

# Blockvalue computation
Profit computed using mininig cost = -0.75 per ton.
(i.e., blockvalue = -0.75 * tonn + process_profit)
Discount rate = 0.15
Type of Constraints:
Process capacity of 10M tons/year and unlimited mining capacity.

# Solution files:
## UPIT
kd_upit.sol
Objective value: 652,195,037
Computed using Hochbaum's pseudoflow algorithm. 

## CPIT
kd_cpit_gmunoz120723.sol
Objective value: 396,858,193 (LP GAP 3.1%)
Provided by Gonzalo Muñoz, and obtained from the LP relaxation using a modified TopoSort heuristic. 

kd.LPcpit
LP relaxation solution (not feasible)
Objective value: 409,498,555
Computed using a modified version of Bienstock & Zuckerberg algorithm. 

## PCPSP
kd_pcpsp_gmunoz120723.sol
Objective value: 406,871,207 (LP GAP 1.0%)
Provided by Gonzalo Muñoz, and obtained from the LP relaxation using a modified TopoSort heuristic

kd.LPpcpsp
LP relaxation solution (not feasible)
Objective value: 410,891,003
Computed using a modified version of Bienstock & Zuckerberg algorithm.