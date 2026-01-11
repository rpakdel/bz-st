# project_spec.md

## 1. Overview

Implement a **Bienstock–Zuckerberg (BZ)** LP relaxation solver in Python for Minelib instances, starting with **`zuck_small`**. Priorities:

1. **Correctness first** on small datasets.
2. Use open-source solvers initially (PuLP + CBC, NetworkX).
3. Add **Streamlit** visualizations for block models, precedence graphs, and solution comparisons.
4. Enforce rigorous **unit and integration testing**.
5. Prepare to switch the master solver to **IBM CPLEX** in later phases.
6. Plan future integration with **MineFlow** or other high-performance closure solvers.

---

## 3. Architecture & Agents

### 3.1 Data Layer (`data-engineer`)
- Parse `.blocks` & `.prec` into `pandas` structures.
- Build `networkx.DiGraph` for precedences (ensure DAG).
- Provide `BlockModel` dataclass with block attributes, capacities, discount info.
- Export caches (Parquet/JSON) for reuse.

### 3.2 Master Problem (`lp-master`)
- Restricted LP via **PuLP** with CBC (default).
- Decision vars = columns (patterns).
- Methods:
  - `initialize(columns)`
  - `solve()`
  - `get_duals()`
  - `add_column(pattern)`
  - `export_solution()`
- Keep solver selection configurable (`cbc` now, `cplex` later).

### 3.3 Pricing Subproblem (`closure-pricer`)
- Convert duals → node weights (profit minus penalties).
- Use `networkx.minimum_cut` for maximum-weight closure.
- Return reduced cost + block selection.
- Maintain backend-agnostic interface to swap in MineFlow CLI later.

### 3.4 Controller (`bz-controller`)
- Loop:
  1. Solve master.
  2. Extract duals.
  3. Run pricing.
  4. Add improving column if reduced cost < −ε.
- Track iteration history, convergence, logging, checkpoints.

### 3.5 Visualization Agent (`streamlit-viz`)
- Streamlit app to display:
  - Dataset overview.
  - 3D block scatter/heatmaps (Plotly/pydeck).
  - Precedence graph snapshots (pyvis/Plotly).
  - BZ iteration progress charts.
  - Comparison table vs. reference objectives.
  - Diagnostics (duals, constraint slacks, column stats).

### 3.6 QA Agent (`qa-analyst`)
- Unit tests per module.
- Integration tests on toy DAGs + `zuck_small`.
- Coverage reports via `pytest-cov`.
- Optional property tests (`hypothesis`).

---

## 4. Tech Stack

- Python ≥ 3.10
- `pandas`, `numpy`
- `networkx`
- `PuLP` (+ CBC packaged solver)
- `scipy` (optional utilities)
- `streamlit`, `plotly`, `pydeck`/`pyvis`
- Testing: `pytest`, `pytest-cov`, `hypothesis` (optional)

Later:
- `docplex` or `cplex` module (when switching to CPLEX).
- MineFlow CLI integration.

---

## 5. Implementation Plan

1. **Setup**
   - Create virtualenv.
   - Install dependencies (`pip install -r requirements-dev.txt`).

2. **Data Loader**
   - Implement `BlockModel` with validation.
   - Cache to `data/intermediate/`.

3. **Master Problem**
   - Build RMP class with PuLP.
   - Seed with initial columns (e.g., trivial feasible pattern or derived from UPIT).

4. **Pricing Subproblem**
   - Map duals to node weights.
   - Solve closure with NetworkX.
   - Return `PricingResult` dataclass.

5. **Controller**
   - Implement iteration loop with logging.
   - Stopping criterion: no column with negative reduced cost within tolerance.

6. **Streamlit App**
   - Layout sections:
     - Sidebar controls (dataset, iteration, filters).
     - Tabs: Overview, Block Model, Precedence Graph, BZ Progress, Solution Comparison, Diagnostics.
   - Use cached data loaders.

7. **Testing**
   - Unit tests for each module.
   - Integration test for `zuck_small` to verify objective against references.
   - CI script (GitHub Actions) to run tests headlessly.

8. **Documentation**
   - Update `README` with usage instructions.
   - Keep `agents.md` as coordination guide.

---

## 6. Testing Strategy

### Unit Tests
- **Data**: schema checks, DAG acyclicity, sample edges.
- **Master**: constraint satisfaction, dual extraction, column addition.
- **Pricing**: known small graphs, reduced-cost sign verification.
- **Controller**: iteration flow on toy example.
- **Visualization Helpers**: deterministic outputs.

### Integration Tests
- **Toy DAG (~10 blocks)**: confirm optimal objective matches closed-form solution.
- **`zuck_small` regression**:
  - Ensure final LP objective ≈ `854,182,396` (CPIT reference) within tolerance.
  - Check column pool size, convergence logs.

### Tools
- `pytest`
- `pytest-cov`
- optional `hypothesis`
- Add `tests/data/` fixtures for toy instances.

---

## 7. Streamlit Details

- File: `app/streamlit_app.py`.
- Use `@st.cache_data` for loaders.
- Visual components:
  - Plotly 3D scatter for blocks (color by value, size by tonnage).
  - Level-by-level precedence slices.
  - Line chart for objective vs. iteration.
  - Table comparing:
    - Our BZ LP values
    - UPIT objective 1,422,726,898
    - CPIT LP 854,182,396
    - PCPSP LP 905,878,172
- Provide download buttons for solution CSVs.

---

## 8. Future Work

1. **Switch Master Solver to CPLEX**
   - Once accuracy confirmed, configure PuLP to call CPLEX (`CPLEX_CMD`) or migrate to `docplex`.
   - Document environment setup for CPLEX license.

2. **Pricing Acceleration**
   - Integrate MineFlow CLI via `subprocess` once interface requirements are clear.
   - Keep NetworkX version for testing.

3. **Larger Datasets**
   - After `zuck_small`, scale to Minelib KD, Marvin, McLaughlin.
   - Profile performance, optimize bundling/stabilization.

---

## 9. References

1. Daniel Bienstock & Mark Zuckerberg (2010). *Solving LP Relaxations of Large-Scale Precedence Constrained Problems.* IPCO 2010: 1–14.
2. Dorit S. Hochbaum (2008). *The Pseudoflow Algorithm: A New Algorithm for the Maximum-Flow Problem.* Operations Research 56(4): 992–1009.
3. Gonzalo Muñoz (2012). *Modelos de optimizacion lineal entera y aplicaciones a la minería.* Master Thesis, Universidad de Chile.
4. `Instance- zuck_small.pdf` (Minelib page snapshot, 2026-01-10 10:45 PM).

---
