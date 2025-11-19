# Task Complexity Bonus API Endpoints

## Overview

This document describes the API endpoints added for Task 3.2: Task Complexity Bonus Calculation.

These endpoints allow calculating bonus components based on the complexity of completed tasks. The system uses a tiered multiplier approach where:
- Simple tasks (complexity 1-3): 0.70-0.85 multiplier
- Medium tasks (complexity 4-6): 0.85-1.00 multiplier
- Complex tasks (complexity 7-10): 1.00-1.30 multiplier

## Endpoints

### 1. Calculate Complexity Bonus (Single Employee KPI)

**Endpoint**: `POST /api/v1/kpi/employee-kpis/{kpi_id}/calculate-complexity`

**Description**: Calculates and updates the complexity bonus component for a single EmployeeKPI record.

**Authentication**: Required (JWT token)

**Path Parameters**:
- `kpi_id` (integer): ID of the EmployeeKPI record

**Process**:
1. Retrieves average complexity of completed tasks for the period (year, month)
2. Calculates complexity multiplier (0.70-1.30)
3. Computes bonus components: `base_bonus × multiplier × (weight/100)`
4. Updates EmployeeKPI fields:
   - `task_complexity_avg`
   - `task_complexity_multiplier`
   - `monthly_bonus_complexity`
   - `quarterly_bonus_complexity`
   - `annual_bonus_complexity`

**Response**: Updated EmployeeKPI object

**Example**:
```bash
curl -X POST "http://localhost:8000/api/v1/kpi/employee-kpis/123/calculate-complexity" \
  -H "Authorization: Bearer {token}"
```

**Response**:
```json
{
  "id": 123,
  "employee_id": 45,
  "year": 2025,
  "month": 11,
  "task_complexity_avg": 7.5,
  "task_complexity_multiplier": 1.15,
  "task_complexity_weight": 20.0,
  "monthly_bonus_base": 50000,
  "monthly_bonus_complexity": 11500,
  ...
}
```

---

### 2. Bulk Calculate Complexity Bonuses

**Endpoint**: `POST /api/v1/kpi/employee-kpis/bulk/calculate-complexity`

**Description**: Mass calculation of complexity bonus components for all EmployeeKPI records in a period.

**Authentication**: Required (JWT token)

**Query Parameters**:
- `year` (integer, required): Year for calculation (2020-2100)
- `month` (integer, required): Month for calculation (1-12)
- `department_id` (integer, optional): Department ID (defaults to current user's department)

**Use Cases**:
- Month-end closing (calculate all bonuses at once)
- Recalculation after task adjustments
- Initialization of complexity bonus system

**Process**:
1. Retrieves all EmployeeKPI records for the period and department
2. For each record:
   - Gets average complexity of completed tasks
   - Calculates complexity multiplier
   - Updates bonus components
3. Returns statistics

**Response**:
```json
{
  "year": 2025,
  "month": 11,
  "department_id": 1,
  "updated_count": 45,
  "skipped_count": 5,
  "total_count": 50,
  "message": "Complexity bonuses calculated successfully"
}
```

**Example**:
```bash
curl -X POST "http://localhost:8000/api/v1/kpi/employee-kpis/bulk/calculate-complexity?year=2025&month=11&department_id=1" \
  -H "Authorization: Bearer {token}"
```

---

### 3. Get Complexity Bonus Breakdown

**Endpoint**: `GET /api/v1/kpi/employee-kpis/{kpi_id}/complexity-breakdown`

**Description**: Returns detailed breakdown of complexity bonus calculation with formulas and task list.

**Authentication**: Required (JWT token)

**Path Parameters**:
- `kpi_id` (integer): ID of the EmployeeKPI record

**Response Includes**:
- List of completed tasks with complexity ratings
- Average complexity
- Complexity tier (simple/medium/complex)
- Calculated multiplier
- Bonus components with formulas

**Example**:
```bash
curl -X GET "http://localhost:8000/api/v1/kpi/employee-kpis/123/complexity-breakdown" \
  -H "Authorization: Bearer {token}"
```

**Response**:
```json
{
  "employee_kpi_id": 123,
  "employee_id": 45,
  "employee_name": "Иванов Иван",
  "period": "2025-11",
  "completed_tasks": [
    {
      "id": 1,
      "title": "Implement authentication",
      "complexity": 8,
      "completed_at": "2025-11-05T10:30:00"
    },
    {
      "id": 2,
      "title": "Add API endpoint",
      "complexity": 7,
      "completed_at": "2025-11-12T15:45:00"
    }
  ],
  "completed_tasks_count": 2,
  "avg_complexity": 7.5,
  "complexity_tier": "complex",
  "complexity_multiplier": 1.15,
  "complexity_weight": 20.0,
  "bonuses": {
    "monthly": {
      "base": 50000,
      "complexity_component": 11500,
      "formula": "50000 × 1.15 × (20/100) = 11500.00"
    },
    "quarterly": {
      "base": 150000,
      "complexity_component": 34500,
      "formula": "150000 × 1.15 × (20/100) = 34500.00"
    },
    "annual": {
      "base": 600000,
      "complexity_component": 138000,
      "formula": "600000 × 1.15 × (20/100) = 138000.00"
    }
  }
}
```

---

## Complexity Multiplier Calculation

The multiplier is calculated based on average task complexity:

| Complexity Range | Tier | Multiplier Range | Description |
|-----------------|------|-----------------|-------------|
| 1.0 - 3.0 | Simple | 0.70 - 0.85 | Routine tasks, penalty multiplier |
| 4.0 - 6.0 | Medium | 0.85 - 1.00 | Standard difficulty |
| 7.0 - 10.0 | Complex | 1.00 - 1.30 | High difficulty, bonus multiplier |

The multiplier is calculated using linear interpolation within each tier.

---

## Bonus Formula

```
complexity_bonus = base_bonus × complexity_multiplier × (complexity_weight / 100)
```

Where:
- `base_bonus`: Base bonus amount for the period (monthly/quarterly/annual)
- `complexity_multiplier`: Calculated multiplier based on average complexity (0.70-1.30)
- `complexity_weight`: Weight of complexity component in total bonus (default: 20%)

---

## Integration with Frontend

These endpoints should be integrated into:

1. **Payroll Calculator** (`PayrollPlanPage.tsx`)
   - Display complexity bonus components
   - Show calculation breakdown
   - Button to recalculate complexity bonuses

2. **KPI Management** (`KpiManagementPage.tsx`)
   - "Calculate Complexity Bonus" button for individual employee KPI
   - "Bulk Calculate" button for period
   - Visual indicators for complexity tier

3. **Employee KPI Details**
   - Display average task complexity
   - Show complexity multiplier
   - Link to detailed breakdown

---

## Access Control

- All endpoints require authentication (JWT token)
- Department access is enforced:
  - USER role: Can only access their own department
  - MANAGER/ADMIN roles: Can access all departments or filter by department

---

## Database Fields

The following fields in the `employee_kpis` table are updated by these endpoints:

| Field | Type | Description |
|-------|------|-------------|
| `task_complexity_avg` | Numeric(5,2) | Average complexity of completed tasks (1-10) |
| `task_complexity_multiplier` | Numeric(5,4) | Calculated multiplier (0.70-1.30) |
| `task_complexity_weight` | Numeric(5,2) | Weight % in total bonus (default: 20) |
| `monthly_bonus_complexity` | Numeric(15,2) | Monthly bonus complexity component |
| `quarterly_bonus_complexity` | Numeric(15,2) | Quarterly bonus complexity component |
| `annual_bonus_complexity` | Numeric(15,2) | Annual bonus complexity component |

---

## Implementation Status

✅ **Task 3.2.3 - Backend API Endpoints**: COMPLETED

- [x] Single employee KPI complexity calculation endpoint
- [x] Bulk calculation endpoint for period/department
- [x] Detailed breakdown endpoint
- [x] Service layer integration (TaskComplexityBonusCalculator)
- [x] Department access control
- [x] Authentication enforcement

⏳ **Next Steps**:
- Task 3.2.4: Update frontend salary calculator to display complexity bonuses
- Task 3.2.5: Add task breakdown visualization in UI
