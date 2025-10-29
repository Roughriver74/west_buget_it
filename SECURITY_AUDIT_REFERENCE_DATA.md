# Security Audit Report: Reference Data API Endpoints
## Date: 2025-10-29
## Files Audited:
1. `/home/user/west_buget_it/backend/app/api/v1/categories.py`
2. `/home/user/west_buget_it/backend/app/api/v1/contractors.py`
3. `/home/user/west_buget_it/backend/app/api/v1/attachments.py`

---

## EXECUTIVE SUMMARY

**Overall Status: 2 CRITICAL VULNERABILITIES + 1 MODERATE ISSUE**

### Summary by File:
- **categories.py**: SECURE ✓ (9/9 endpoints pass security checks)
- **contractors.py**: VULNERABLE ✗ (2/8 endpoints have vulnerabilities)
- **attachments.py**: CRITICAL ✗ (6/6 endpoints have critical vulnerabilities)

---

## DETAILED FINDINGS

### 1. CATEGORIES.PY
**Status: SECURE ✓**

#### Endpoints Reviewed (9 total):

| Endpoint | Method | Department Check | Role Filtering | Status |
|----------|--------|------------------|-----------------|--------|
| GET / | GET | ✓ Lines 50-61 | ✓ Lines 50-61 | SECURE |
| GET /{category_id} | GET | ✓ Lines 106-111 | ✓ Lines 106-111 | SECURE |
| POST / | POST | ✓ Lines 154-164 | ✓ Lines 154-164 | SECURE |
| PUT /{category_id} | PUT | ✓ Lines 190-195 | ✓ Lines 190-195 | SECURE |
| DELETE /{category_id} | DELETE | ✓ Lines 231-236 | ✓ Lines 231-236 | SECURE |
| POST /bulk/update | POST | ✓ Lines 261-267 + 271-275 | ✓ Lines 261-267 | SECURE |
| POST /bulk/delete | DELETE | ✓ Lines 308-314 + 319-323 | ✓ Lines 308-314 | SECURE |
| GET /export | GET | ✓ Lines 348-354 | ✓ Lines 348-354 | SECURE |
| POST /import | POST | ✓ Lines 469 | ✓ Lines 469 | SECURE |

**Key Security Features:**
- USER role strictly limited to their own department (Line 50-57)
- MANAGER/ADMIN can optionally filter by department_id parameter (Line 58-61)
- Bulk operations validate that ALL requested IDs are accessible (Line 271-275 & 319-323)
- Excel import forces current_user.department_id (Line 469)

**Security Pattern (CORRECT):**
```python
if current_user.role == UserRoleEnum.USER:
    query = query.filter(BudgetCategory.department_id == current_user.department_id)
elif current_user.role in [UserRoleEnum.MANAGER, UserRoleEnum.ADMIN]:
    if department_id is not None:
        query = query.filter(BudgetCategory.department_id == department_id)
```

---

### 2. CONTRACTORS.PY
**Status: VULNERABLE ✗**

#### Endpoints Reviewed (8 total):

| Endpoint | Method | Department Check | Role Filtering | Status | Issue |
|----------|--------|------------------|-----------------|--------|-------|
| GET / | GET | ✓ Lines 49-60 | ✓ Lines 49-60 | SECURE | - |
| GET /{contractor_id} | GET | ✓ Lines 111-116 | ✓ Lines 111-116 | SECURE | - |
| POST / | POST | ✓ Lines 160-170 | ✓ Lines 160-170 | SECURE | - |
| PUT /{contractor_id} | PUT | ✓ Lines 196-201 | ✓ Lines 196-201 | SECURE | - |
| DELETE /{contractor_id} | DELETE | ✓ Lines 229-234 | ✓ Lines 229-234 | SECURE | - |
| POST /bulk/update | POST | ✓ Lines 253-259 | ✓ Lines 253-259 | **VULNERABLE** | No validation that all IDs found |
| POST /bulk/delete | DELETE | ✓ Lines 286-292 | ✓ Lines 286-292 | **VULNERABLE** | No validation that all IDs found |
| GET /export | GET | ✓ Lines 317-323 | ✓ Lines 317-323 | SECURE | - |
| POST /import | POST | ✓ Line 433 | ✓ Line 433 | SECURE | - |

---

### VULNERABILITY #1: Contractors - Missing Bulk Operation Validation
**Severity: MODERATE**
**Type: Information Disclosure + Silent Failure**
**Location: contractors.py, lines 243-273 (bulk_update) and 276-305 (bulk_delete)**

#### Issue Description:
Both `bulk_update_contractors` and `bulk_delete_contractors` endpoints lack validation that ALL requested contractor IDs were successfully found and processed. This creates two problems:

1. **Silent Failure**: If a USER requests to update contractors [1, 2, 3] but only [1, 2] are in their department, the function will silently update only those two and return the count (2) alongside the FULL list of request IDs [1, 2, 3], creating inconsistency.

2. **Information Disclosure**: The response doesn't indicate which IDs could not be accessed. In a security-conscious system, this could reveal:
   - Which contractor IDs exist in OTHER departments
   - A discrepancy between request and action

#### Code Analysis:

**VULNERABLE CODE - bulk_update (Line 243-273):**
```python
@router.post("/bulk/update", status_code=status.HTTP_200_OK)
def bulk_update_contractors(
    request: BulkUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Bulk activate/deactivate contractors"""
    query = db.query(Contractor).filter(Contractor.id.in_(request.ids))

    if current_user.role == UserRoleEnum.USER:
        if not current_user.department_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, ...)
        query = query.filter(Contractor.department_id == current_user.department_id)

    contractors = query.all()
    
    # MISSING VALIDATION HERE: Should check len(contractors) == len(request.ids)
    # Currently proceeds with partial updates without error

    for contractor in contractors:
        contractor.is_active = request.is_active

    db.commit()
    return {
        "updated_count": len(contractors),  # May be less than len(request.ids)
        "ids": request.ids,                  # Full list, misleading response
        "is_active": request.is_active
    }
```

**VULNERABLE CODE - bulk_delete (Line 276-305):**
```python
@router.post("/bulk/delete", status_code=status.HTTP_200_OK)
def bulk_delete_contractors(
    request: BulkDeleteRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Bulk delete contractors (permanently remove from database)"""
    query = db.query(Contractor).filter(Contractor.id.in_(request.ids))

    if current_user.role == UserRoleEnum.USER:
        if not current_user.department_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, ...)
        query = query.filter(Contractor.department_id == current_user.department_id)

    contractors = query.all()
    
    # MISSING VALIDATION HERE: Should check len(contractors) == len(request.ids)

    for contractor in contractors:
        db.delete(contractor)

    db.commit()
    return {
        "deleted_count": len(contractors),   # May be less than len(request.ids)
        "ids": request.ids                   # Full list returned regardless
    }
```

#### Comparison to CORRECT Implementation (categories.py, lines 318-323):
```python
categories = query.all()

# CORRECT: Validates all requested IDs were found and accessible
if len(categories) != len(request.ids):
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Some categories not found or not accessible"
    )
```

#### Impact:
- **Risk**: Client may not realize their bulk update/delete was only partially executed
- **Inconsistency**: Response includes full request IDs but only partial count
- **Potential Exploit**: Could be used to enumerate contractors in other departments (if someone notices count mismatch)

#### Recommendation:
Add validation after line 261 (bulk_update) and line 294 (bulk_delete):
```python
if len(contractors) != len(request.ids):
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Some contractors not found or not accessible"
    )
```

---

### 3. ATTACHMENTS.PY
**Status: CRITICAL VULNERABILITY ✗**

#### Endpoints Reviewed (6 total):

| Endpoint | Method | Expense Exists Check | Department Check for USER | Cross-Dept Data Leak | Status |
|----------|--------|----------------------|---------------------------|----------------------|--------|
| POST /{expense_id}/attachments | POST | ✓ Lines 53-58 | **✗ MISSING** | **YES** | **CRITICAL** |
| GET /{expense_id}/attachments | GET | ✓ Lines 119-124 | **✗ MISSING** | **YES** | **CRITICAL** |
| GET /attachments/{attachment_id} | GET | ✓ Lines 142-147 | **✗ MISSING** | **YES** | **CRITICAL** |
| GET /attachments/{attachment_id}/download | GET | ✓ Lines 160-165 | **✗ MISSING** | **YES** | **CRITICAL** |
| PATCH /attachments/{attachment_id} | PATCH | ✓ Lines 190-195 | **✗ MISSING** | **YES** | **CRITICAL** |
| DELETE /attachments/{attachment_id} | DELETE | ✓ Lines 216-221 | **✗ MISSING** | **YES** | **CRITICAL** |

---

### VULNERABILITY #2: Attachments - Complete Absence of Department Validation
**Severity: CRITICAL**
**Type: Cross-Department Data Breach / Unauthorized Access**
**Location: attachments.py, ALL 6 ENDPOINTS**
**CWE-639: Authorization Bypass Through User-Controlled Key**

#### Issue Description:
**EVERY endpoint in attachments.py is missing critical department-level access control.** While endpoints verify that an expense exists, they DO NOT verify that the expense belongs to the current user's department. This allows a USER role user to:

1. **Upload files to ANY expense in ANY department** (line 41-107)
2. **View files from ANY expense in ANY department** (line 110-131 & 134-149)
3. **Download files from ANY department** (line 152-178)
4. **Modify metadata of files from ANY department** (line 181-205)
5. **Delete files from ANY department** (line 208-236)

#### Database Model Context:
From `/home/user/west_buget_it/backend/app/db/models.py`:
- **Attachment model (line 349-370)**: Has NO department_id field
- **Links to Expense via**: `expense_id` foreign key (line 356)
- **Expense model (line 220-269)**: HAS `department_id` field (line 232)

**The fix requires traversing:** Attachment → Expense.department_id → Check against current_user.department_id

---

### VULNERABILITY #2a: POST /{expense_id}/attachments - File Upload to Any Department
**Severity: CRITICAL**
**Location: attachments.py, lines 41-107**

#### Vulnerable Code:
```python
@router.post("/{expense_id}/attachments", response_model=AttachmentInDB, status_code=status.HTTP_201_CREATED)
async def upload_attachment(
    expense_id: int,
    file: UploadFile = File(...),
    file_type: str = Form(None),
    uploaded_by: str = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Upload a file attachment for an expense"""

    # Check if expense exists (LINE 53)
    expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Expense with id {expense_id} not found"
        )
    
    # MISSING: Department validation
    # if current_user.role == UserRoleEnum.USER:
    #     if expense.department_id != current_user.department_id:
    #         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, ...)

    # File validation passes
    if not is_allowed_file(file.filename):
        raise HTTPException(...)

    content = await file.read()
    
    # ... file saved to disk ...
    
    db_attachment = Attachment(
        expense_id=expense_id,  # Could be ANY expense
        filename=file.filename,
        file_path=str(file_path),
        file_size=file_size,
        mime_type=file.content_type,
        file_type=file_type,
        uploaded_by=uploaded_by
    )

    db.add(db_attachment)
    db.commit()
    return db_attachment
```

#### Attack Scenario:
1. Attacker has USER role in Department A
2. Discovers an expense ID (e.g., 999) from Department B
3. Calls `POST /api/v1/attachments/999/attachments`
4. Attaches a PDF file to Department B's expense
5. Success: File is uploaded and stored!

#### Impact:
- Unauthorized file attachment to expenses outside user's department
- Potential file injection attacks
- Corrupting other departments' records

---

### VULNERABILITY #2b: GET /{expense_id}/attachments - View Files from Any Department
**Severity: CRITICAL**
**Location: attachments.py, lines 110-131**

#### Vulnerable Code:
```python
@router.get("/{expense_id}/attachments", response_model=AttachmentList)
def get_expense_attachments(
    expense_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all attachments for an expense"""

    # Check if expense exists (LINE 119)
    expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not expense:
        raise HTTPException(...)

    # MISSING: Department validation
    # if current_user.role == UserRoleEnum.USER:
    #     if expense.department_id != current_user.department_id:
    #         raise HTTPException(...)

    attachments = db.query(Attachment).filter(Attachment.expense_id == expense_id).all()

    return AttachmentList(
        items=attachments,
        total=len(attachments)
    )
```

#### Attack Scenario:
1. User from Department A enumerates expense IDs
2. Finds expense 999 from Department B (via error messages, timing, or knowledge)
3. Calls `GET /api/v1/attachments/999/attachments`
4. Receives full list of files attached to Department B's expense
5. Data breach: Can now view metadata about files in other departments

#### Impact:
- Information disclosure about other departments' expenses
- Ability to enumerate expenses across departments
- Discovery of sensitive document types/names

---

### VULNERABILITY #2c: GET /attachments/{attachment_id} - View Attachment Metadata from Any Department
**Severity: CRITICAL**
**Location: attachments.py, lines 134-149**

#### Vulnerable Code:
```python
@router.get("/attachments/{attachment_id}", response_model=AttachmentInDB)
def get_attachment(
    attachment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get attachment by ID"""

    attachment = db.query(Attachment).filter(Attachment.id == attachment_id).first()
    if not attachment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Attachment with id {attachment_id} not found"
        )
    
    # MISSING: Department validation through expense.department_id
    # expense = db.query(Expense).filter(Expense.id == attachment.expense_id).first()
    # if current_user.role == UserRoleEnum.USER:
    #     if expense.department_id != current_user.department_id:
    #         raise HTTPException(...)

    return attachment
```

#### Attack Scenario:
1. Attacker enumerates attachment IDs
2. For each ID, calls `GET /api/v1/attachments/{id}`
3. Returns filename, file_type, mime_type, file_size, upload_date, uploaded_by
4. Successfully maps confidential information about other departments' files

#### Impact:
- Direct enumeration attack on attachment IDs
- Disclosure of sensitive file metadata
- Cross-department information gathering

---

### VULNERABILITY #2d: GET /attachments/{attachment_id}/download - Download Files from Any Department
**Severity: CRITICAL (MOST DANGEROUS)**
**Location: attachments.py, lines 152-178**

#### Vulnerable Code:
```python
@router.get("/attachments/{attachment_id}/download")
def download_attachment(
    attachment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Download an attachment file"""

    attachment = db.query(Attachment).filter(Attachment.id == attachment_id).first()
    if not attachment:
        raise HTTPException(...)

    # MISSING: Department validation
    # expense = db.query(Expense).filter(Expense.id == attachment.expense_id).first()
    # if current_user.role == UserRoleEnum.USER:
    #     if expense.department_id != current_user.department_id:
    #         raise HTTPException(...)

    file_path = Path(attachment.file_path)
    if not file_path.exists():
        raise HTTPException(...)

    return FileResponse(
        path=file_path,
        filename=attachment.filename,
        media_type=attachment.mime_type or 'application/octet-stream'
    )
```

#### Attack Scenario:
1. Attacker from Department A discovers attachment ID 42
2. Calls `GET /api/v1/attachments/42/download`
3. Receives actual file content (e.g., another department's contract, budget document, invoice)
4. **Data exfiltration complete**

#### Impact:
- **HIGHEST RISK**: Direct access to sensitive files from other departments
- Download of confidential contracts, invoices, budgets
- Complete bypass of multi-tenancy isolation
- Compliance violation (GDPR, data protection regulations)

---

### VULNERABILITY #2e: PATCH /attachments/{attachment_id} - Modify Files from Any Department
**Severity: CRITICAL**
**Location: attachments.py, lines 181-205**

#### Vulnerable Code:
```python
@router.patch("/attachments/{attachment_id}", response_model=AttachmentInDB)
def update_attachment(
    attachment_id: int,
    attachment_update: AttachmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update attachment metadata (filename or file_type)"""

    attachment = db.query(Attachment).filter(Attachment.id == attachment_id).first()
    if not attachment:
        raise HTTPException(...)

    # MISSING: Department validation
    # expense = db.query(Expense).filter(Expense.id == attachment.expense_id).first()
    # if current_user.role == UserRoleEnum.USER:
    #     if expense.department_id != current_user.department_id:
    #         raise HTTPException(...)

    update_data = attachment_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(attachment, field, value)

    db.commit()
    db.refresh(attachment)

    return attachment
```

#### Attack Scenario:
1. Attacker from Department A discovers attachment ID 42
2. Calls `PATCH /api/v1/attachments/42` with `{"file_type": "FAKE", "filename": "modified.pdf"}`
3. Metadata is updated in database
4. Department B's records are corrupted

#### Impact:
- Unauthorized modification of other departments' records
- Data integrity violation
- Audit trail corruption

---

### VULNERABILITY #2f: DELETE /attachments/{attachment_id} - Delete Files from Any Department
**Severity: CRITICAL**
**Location: attachments.py, lines 208-236**

#### Vulnerable Code:
```python
@router.delete("/attachments/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_attachment(
    attachment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete an attachment"""

    attachment = db.query(Attachment).filter(Attachment.id == attachment_id).first()
    if not attachment:
        raise HTTPException(...)

    # MISSING: Department validation
    # expense = db.query(Expense).filter(Expense.id == attachment.expense_id).first()
    # if current_user.role == UserRoleEnum.USER:
    #     if expense.department_id != current_user.department_id:
    #         raise HTTPException(...)

    # Delete file from disk
    file_path = Path(attachment.file_path)
    if file_path.exists():
        try:
            os.remove(file_path)  # File deleted from system!
        except Exception as e:
            print(f"Error deleting file {file_path}: {e}")

    # Delete database record
    db.delete(attachment)
    db.commit()

    return None
```

#### Attack Scenario:
1. Attacker from Department A discovers critical attachment ID (e.g., contract from Department B)
2. Calls `DELETE /api/v1/attachments/{id}`
3. File is PERMANENTLY deleted from both disk and database
4. Destruction of evidence/important documents

#### Impact:
- **Data destruction**: Files deleted from disk permanently
- **Record deletion**: Database records removed
- **Sabotage**: Competitors or malicious actors could destroy other departments' critical files
- **Compliance violation**: Deleted audit trail

---

## CORRECT IMPLEMENTATION PATTERN

Based on expenses.py (lines 256-282), the correct pattern for department validation is:

```python
from app.db.models import Expense, UserRoleEnum, User
from sqlalchemy.orm import Session

def validate_expense_access(expense_id: int, current_user: User, db: Session):
    """Helper to validate user can access an expense"""
    expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Expense with id {expense_id} not found"
        )
    
    # Check department access for USER role
    if current_user.role == UserRoleEnum.USER:
        if expense.department_id != current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You can only view expenses from your own department"
            )
    
    return expense
```

#### For Attachment Endpoints:

```python
def validate_attachment_access(attachment_id: int, current_user: User, db: Session):
    """Helper to validate user can access an attachment"""
    from app.db.models import Attachment
    
    attachment = db.query(Attachment).filter(Attachment.id == attachment_id).first()
    if not attachment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Attachment with id {attachment_id} not found"
        )
    
    # Get the related expense and check department access
    expense = db.query(Expense).filter(Expense.id == attachment.expense_id).first()
    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Related expense not found"
        )
    
    if current_user.role == UserRoleEnum.USER:
        if expense.department_id != current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Attachment belongs to a different department"
            )
    
    return attachment, expense
```

---

## RECOMMENDATIONS & FIXES

### Priority 1: CRITICAL (Fix Immediately)

#### For attachments.py - Add Department Validation to ALL 6 Endpoints:

**Step 1: Add validation helper after line 38:**
```python
from app.db.models import UserRoleEnum, Expense

def validate_attachment_department_access(attachment: Attachment, current_user: User, db: Session):
    """Validate user has access to attachment's expense"""
    expense = db.query(Expense).filter(Expense.id == attachment.expense_id).first()
    if not expense:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Related expense not found"
        )
    
    if current_user.role == UserRoleEnum.USER:
        if expense.department_id != current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Attachment belongs to a different department"
            )
    
    return expense
```

**Step 2: Update ALL endpoints to validate expense department:**

1. **POST /{expense_id}/attachments (Line 41)**: After line 58, add:
   ```python
   # Validate USER can only upload to their own department
   if current_user.role == UserRoleEnum.USER:
       if expense.department_id != current_user.department_id:
           raise HTTPException(
               status_code=status.HTTP_403_FORBIDDEN,
               detail="Access denied: Can only attach files to expenses in your department"
           )
   ```

2. **GET /{expense_id}/attachments (Line 110)**: After line 124, add:
   ```python
   # Validate USER can only view attachments from their department
   if current_user.role == UserRoleEnum.USER:
       if expense.department_id != current_user.department_id:
           raise HTTPException(
               status_code=status.HTTP_403_FORBIDDEN,
               detail="Access denied: Can only view attachments from your department"
           )
   ```

3. **GET /attachments/{attachment_id} (Line 134)**: After line 147, add:
   ```python
   validate_attachment_department_access(attachment, current_user, db)
   ```

4. **GET /attachments/{attachment_id}/download (Line 152)**: After line 165, add:
   ```python
   validate_attachment_department_access(attachment, current_user, db)
   ```

5. **PATCH /attachments/{attachment_id} (Line 181)**: After line 195, add:
   ```python
   validate_attachment_department_access(attachment, current_user, db)
   ```

6. **DELETE /attachments/{attachment_id} (Line 208)**: After line 221, add:
   ```python
   validate_attachment_department_access(attachment, current_user, db)
   ```

---

### Priority 2: MODERATE (Fix Within 1 Week)

#### For contractors.py - Add Bulk Operation Validation:

**Fix bulk_update_contractors (Line 261):** Add after line 261:
```python
contractors = query.all()

# Validate all requested IDs were found and accessible
if len(contractors) != len(request.ids):
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Some contractors not found or not accessible"
    )
```

**Fix bulk_delete_contractors (Line 294):** Add after line 294:
```python
contractors = query.all()

# Validate all requested IDs were found and accessible
if len(contractors) != len(request.ids):
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Some contractors not found or not accessible"
    )
```

---

## COMPLIANCE IMPACT

### Violated Security Principles (from CLAUDE.md):
1. **✗ Multi-Tenancy**: Attachments lack department_id filtering
2. **✗ Role-Based Access Control**: No USER role restrictions in attachments.py
3. **✗ Data Isolation**: Files from any department accessible by any user

### Regulatory Impact:
- **GDPR**: Unauthorized access to personal data in other departments
- **Data Protection Acts**: Breaches multi-tenancy isolation requirements
- **SOX/Internal Controls**: Lacks proper access controls for sensitive documents
- **Audit Trail**: Cross-department modifications not properly restricted

---

## TESTING RECOMMENDATIONS

### Security Test Cases:

1. **Department Isolation Test - POST /attachments/{expense_id}/attachments**
   - Create expense in Department A
   - Login as USER in Department B
   - Try to upload file to Department A's expense
   - Expected: 403 FORBIDDEN
   - Current: 201 CREATED ✗ (VULNERABLE)

2. **Cross-Department Download Test - GET /attachments/{id}/download**
   - Get attachment ID from Department A
   - Login as USER in Department B
   - Try to download attachment
   - Expected: 403 FORBIDDEN
   - Current: 200 OK + file contents ✗ (VULNERABLE)

3. **Bulk Update Validation - POST /contractors/bulk/update**
   - Request IDs [1, 2, 3] where only [1, 2] exist in user's department
   - Expected: 404 with "Some contractors not found"
   - Current: 200 with updated_count=2 ✗ (VULNERABLE)

---

## SUMMARY TABLE

| File | Endpoint | Issue | Severity | Line(s) | Fix Priority |
|------|----------|-------|----------|---------|--------------|
| categories.py | All | None | - | - | - |
| contractors.py | POST /bulk/update | Missing validation | MODERATE | 261 | P2 |
| contractors.py | POST /bulk/delete | Missing validation | MODERATE | 294 | P2 |
| attachments.py | POST /{id}/attachments | No dept check | CRITICAL | 41-107 | P1 |
| attachments.py | GET /{id}/attachments | No dept check | CRITICAL | 110-131 | P1 |
| attachments.py | GET /attachments/{id} | No dept check | CRITICAL | 134-149 | P1 |
| attachments.py | GET /attachments/{id}/download | No dept check | CRITICAL | 152-178 | P1 |
| attachments.py | PATCH /attachments/{id} | No dept check | CRITICAL | 181-205 | P1 |
| attachments.py | DELETE /attachments/{id} | No dept check | CRITICAL | 208-236 | P1 |

---

## CONCLUSION

**IMMEDIATE ACTION REQUIRED ON ATTACHMENTS.PY**

The attachments.py module contains 6 critical vulnerabilities that allow complete bypass of the multi-tenancy system. Users can:
- Download confidential files from other departments
- Delete important documents from other departments  
- Modify records in other departments
- Upload unauthorized files to other departments

This is a **data breach risk** and must be fixed immediately before system goes to production.

**Secondary Issue**: contractors.py bulk operations lack validation for consistency with categories.py implementation.

All fixes are straightforward - adding department_id checks following the established pattern from expenses.py and categories.py.

