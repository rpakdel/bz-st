# Marvin test mine

## Block model:
Block size: 30x30x30 meters
Precedence computed with 45 degrees using 8 levels

## Blockfile columns detail:
<id> <x> <y> <z> <tonn> <au [ppm]> <cu %> <proc_profit>

## Blockvalue computation
Blockvalues computed using mine cost = 0.9 per ton.
proc_profit = (AU * Rec_Au * (Price_AU - Selling_AU)) + (CU * Rec_CU * (Price_CU - Selling_CU)) - Proc_cost
where Rec_AU = 0.6, Rec_CU = 0.88, Price_AU = 12, Selling_AU = 0.2, Price_CU = 20, Selling_CU = 7.2 and Proc_cost = 4.0
Discount rate = 0.1
UPIT/CPIT profit computed processing blocks with <proc_profit> > 0
Type of Constraints:
C0 Capacity constraint (mine): Total extracted tonnage < 60M
C1 Capacity constraint (process): Total processed tonnage < 20M

# Solution files:
## UPIT
marvin_upit.sol
Objective value: 1,415,655,436
Computed using Hochbaum's pseudoflow algorithm. 

## CPIT
marvin_cpit_gmunoz120723.sol
Objective value: 820,726,048 (LP GAP 5.0%)
Provided by Gonzalo Muñoz, and obtained from the LP relaxation using a modified TopoSort heuristic. 

marvin.LPcpit
LP relaxation solution (not feasible)
Objective value: 863,916,131
Computed using a modified version of Bienstock & Zuckerberg algorithm. 

## PCPSP
marvin_pcpsp_gmunoz120723.sol
Objective value: 885,968,070 (LP GAP 2.8%)
Provided by Gonzalo Muñoz, and obtained from the LP relaxation using a modified TopoSort heuristic.

marvin.LPpcpsp
LP relaxation solution (not feasible)
Objective value: 911,704,665
Computed using a modified version of Bienstock & Zuckerberg algorithm.


# Mine Information
Block size 23000 m³ (X = 30m, Y=30m, Z=30m)
AU - Selling Price 12 $/g
AU - Selling Cost 0.2 $/g
AU - Recovery 0.60
CU - Selling Price 2000 $/ton
CU - Selling Cost 720 $/ton
CU - Recovery 0.88
Mining Cost 0.9 $/ton 
Processing Cost 4.0 $/ton
Discount Rate 10% per year
Default Density 2.75 t/m³
Default Slope Angles 45 degrees

# Constraints
Processing capacity 10 Mt per year
Total movement 40 Mt per year
Sum of processing hours 4,000 per year (detailed estimate of the plant throughput)
Vertical rate of advance: 150m per year
Copper grade Limited until 0.7%
Minimum Mining Width 50m
Minimum Bottom Width 100m
Restrict Mining Surface Some surface in .csv format. For example due to a processing plant in the area.
Fixed Mining (Stockpiling) 0.9$/t
Rehandling cost (Stockpiling) 0.2$/t

# Economic Values
Process Function = BlockSize * Density * [GradeCU/100 * RecoveryCu * (SellingPriceCU – SellingCostCU) + GradeAU * RecoveryCu * (SellingPriceAU – SellingCostAU) - (ProcessingCost + MiningCost)]

Waste Function = BlockSize * Density * MiningCost