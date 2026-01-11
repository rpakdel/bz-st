```markdown
# MineLib File Format Specification  

**Instructions for an AI Coding Agent**

This document defines how to parse, validate, and use MineLib input files for open-pit mining optimization problems. Follow these instructions strictly when implementing readers, validators, or model builders.

---

## 1. Overview

MineLib is a public library of benchmark instances for open-pit mining optimization, similar to MIPLIB. Each instance consists of **three ASCII text files**:

1. **Block-Model Descriptor File** – geological block data  
2. **Block-Precedence Descriptor File** – mining precedence relationships  
3. **Optimization-Model Descriptor File** – data required to formulate optimization models

Supported problem types:
- **UPIT**: Ultimate Pit Problem  
- **CPIT**: Constrained Pit Limit Problem  
- **PCPSP**: Precedence Constrained Production Scheduling Problem  

---

## 2. General Parsing Rules (Applies to All Files)

- Files are **ASCII text**.
- Lines beginning with `%` are **comments** and must be ignored.
- Fields are separated by:
  - Space (ASCII 32)
  - Horizontal tab (ASCII 9)
  - Colon `:` (ASCII 58)
- Leading separators are ignored.
- Multiple contiguous separators count as **one separator**.
- Entries appear **in the order specified** in this document.
- Data types:
  - `<str>`: string without separators
  - `<int>`: integer
  - `<dbl>`: floating-point number
  - `<char>`: single character

---

## 3. Block-Model Descriptor File

### Purpose
Defines geological and economic attributes of each block.

### Structure
- One line per block
- All lines have the same number of columns

### Line Format
```
<int id> <int x> <int y> <int z> <str1> ... <strk>
```

### Semantics
- `id`: unique block identifier, starting from 0
- `x, y, z`: block coordinates  
  - `z = 0` is the bottom-most level  
  - `z` increases upward  
- `str1...strk`: user-defined attributes (e.g., tonnage, grade, impurities)
  - Types must be declared beforehand
  - Values must follow delimiter rules

---

## 4. Block-Precedence Descriptor File

### Purpose
Defines precedence (dependency) relationships between blocks.

### Structure
- One line per block
- Each block appears **at most once**

### Line Format
```
<int b> <int n> <int p1> ... <int pn>
```

### Semantics
- `b`: block identifier
- `n`: number of predecessor blocks
- `p1...pn`: identifiers of predecessor blocks
- If `n = 0`, no predecessors are listed
- Predecessors are typically immediate, but this is **not strictly required**

---

## 5. Optimization-Model Descriptor File

### Purpose
Contains all information needed to formulate UPIT, CPIT, or PCPSP models.

---

## 5.1 Concepts and Notation (For Model Construction)

- `B = {1,...,n}`: set of blocks
- `P(a)`: predecessors of block `a`
- `tmax`: number of time periods
- `dmax`: number of destinations
- `rmax`: number of resources
- `qbr`, `qbrd`: resource usage coefficients
- `Rrt`, `R̄rt`: resource limits
- `A`, `a`: general constraint matrix and bounds

---

## 5.2 File Sections (Must Appear in Order)

### 5.2.1 NAME
```
NAME: <str>
```
Identifies the instance.

---

### 5.2.2 TYPE
```
TYPE: <str>
```
Must be one of:
- `UPIT`
- `CPIT`
- `PCPSP`

---

### 5.2.3 NBLOCKS
```
NBLOCKS: <int n>
```

---

### 5.2.4 NPERIODS
```
NPERIODS: <int tmax>
```
Required for `CPIT` and `PCPSP`.

---

### 5.2.5 NDESTINATIONS
```
NDESTINATIONS: <int dmax>
```
Required for `PCPSP`.

---

### 5.2.6 NRESOURCE SIDE CONSTRAINTS
```
NRESOURCE SIDE CONSTRAINTS: <int rmax>
```
Required for `CPIT` and `PCPSP`.

---

### 5.2.7 NGENERAL SIDE CONSTRAINTS
```
NGENERAL SIDE CONSTRAINTS: <int m>
```
Required for `PCPSP`.

---

### 5.2.8 DISCOUNT RATE
```
DISCOUNT RATE: <dbl δ>
```
Used to discount profits:
- `pbt = pb / (1 + δ)^t`
- `pbdt = pbd / (1 + δ)^t`

---

### 5.2.9 OBJECTIVE FUNCTION

- Exactly `NBLOCKS` lines
- If `TYPE` is `UPIT` or `CPIT`, assume `NDESTINATIONS = 1`

#### Line Format
```
<int b> <dbl pb1> ... <dbl pbdmax>
```

- `b`: block identifier
- `pb_d`: profit for block `b` sent to destination `d`
- Block identifiers must be unique

---

### 5.2.10 RESOURCE CONSTRAINT COEFFICIENTS

Defines nonzero coefficients in resource constraints.

#### Line Formats
```
<int b> <int r> <dbl v>
```
or
```
<int b> <int d> <int r> <dbl v>
```

- `v` corresponds to `qbr` or `qbrd`
- All unspecified coefficients default to zero

---

### 5.2.11 RESOURCE CONSTRAINT LIMITS

Defines bounds for each resource and time period.

#### Line Formats
```
<int r> <int t> <char c> <dbl v1>
```
or
```
<int r> <int t> <char c> <dbl v1> <dbl v2>
```

- `c` ∈ `{L, G, I}`
  - `L`: ≤ v1
  - `G`: ≥ v1
  - `I`: v1 ≤ · ≤ v2
- No defaults allowed; missing limits make the instance invalid

---

### 5.2.12 GENERAL CONSTRAINT COEFFICIENTS (PCPSP only)

Defines nonzero entries of matrix `A`.

#### Line Format
```
<int b> <int d> <int t> <int j> <dbl v>
```

- `j`: row index of matrix `A`
- All unspecified coefficients default to zero

---

### 5.2.13 GENERAL CONSTRAINT LIMITS (PCPSP only)

Defines bounds for each general constraint.

#### Line Formats
```
<int m> <char c> <dbl v1>
```
or
```
<int m> <char c> <dbl v1> <dbl v2>
```

- Same semantics for `c` as resource constraints (`L`, `G`, `I`)
- No default bounds allowed

---

## 6. Validation Rules for AI Agent

- Enforce strict section ordering.
- Validate that all required sections exist for the specified `TYPE`.
- Ensure:
  - Unique block identifiers where required
  - All referenced blocks, periods, destinations, and resources are in range
  - No missing constraint limits
- Treat all undefined coefficients as zero.
- Reject instances that violate any structural rule.

---

## 7. Intended Usage

Use this specification to:
- Build parsers for MineLib instances
- Validate data integrity
- Automatically generate UPIT, CPIT, or PCPSP optimization models
- Interface MineLib data with MILP solvers
```