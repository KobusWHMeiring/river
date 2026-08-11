# UAT: Participant Count + Typeable Litter Bags

**Feature:** `quick-specs-participants-typeable.md`
**Date:** 2026-08-11

---

## Pre-Test Setup

- [ ] Database migrated: `python manage.py migrate`
- [ ] Dev server running: `python manage.py runserver`
- [ ] Logged in as admin user

---

## Scenario 1: Log a visit with participant count — happy path

1. Navigate to a planner view (Weekly or Monthly)
2. Click a day cell to open "Add Task" modal
3. Create a Litter Run task
4. Click the task to open "Add Log"
5. In Core Details, enter **5** in the "Number of Participants" field
6. Enter **3** in General Litter Bags (type directly)
7. Enter **2** in Recyclable Bags (type directly)
8. Submit the form

**Expected:**
- Form submits without errors
- Navigate to Dashboard → Participants card shows **5 People**
- Dashboard shows **3 General / 2 Recyclable** bags

---

## Scenario 2: Multiple visits — aggregation

1. Create a second visit log with **3** participants
2. Create a third visit log with **0** participants (leave at default)

**Expected:**
- Dashboard Participants card shows **8 People** (5 + 3 + 0)
- Total is a proper Sum(), not a Count() of visits

---

## Scenario 3: Edit an existing visit log

1. Open the first visit log for editing
2. Change Participants from **5** to **10**
3. Change General Litter Bags from **3** to **7** (type directly)
4. Submit

**Expected:**
- Dashboard shows **13 People** (10 + 3 + 0)
- Dashboard shows **7 General** bags for that visit's contribution

---

## Scenario 4: Zero participants (default)

1. Create a new visit log without touching the Participants field
2. Submit

**Expected:**
- Form submits without errors
- Dashboard total participants unchanged (includes the implicit 0)

---

## Scenario 5: Type large numbers directly

1. Create a new visit log
2. Type **150** directly into General Litter Bags
3. Type **75** directly into Recyclable Bags
4. Submit

**Expected:**
- Values persist in dashboard totals
- No validation errors

---

## Scenario 6: Negative values blocked

1. Create a new visit log
2. Try to type **-5** into the Participants field using the browser's down-arrow

**Expected:**
- Browser blocks negative values (HTML `min="0"`)
- If user somehow submits a negative value, Django `PositiveIntegerField` rejects it

---

## Scenario 7: Existing visit logs not broken

1. Verify existing visit logs (created before this feature) still display correctly
2. Edit an old visit log → Participants should show **0** (migration default)
3. Dashboard aggregation works with mixed old (0) and new (N) values

---

## Data Integrity Checks

Run in Django shell (`python manage.py shell`):

```python
# 1. Migration applied correctly
from django.db import connection
tables = connection.introspection.get_table_description(connection.cursor(), 'core_visitlog')
fields = [f.name for f in tables]
assert 'participant_count' in fields, "participant_count column missing!"

# 2. Existing rows default to 0
from core.models import VisitLog
null_participants = VisitLog.objects.filter(participant_count__isnull=True).count()
assert null_participants == 0, f"Found {null_participants} rows with NULL participant_count"

# 3. Aggregation works
from django.db.models import Sum
total = VisitLog.objects.aggregate(Sum('participant_count'))['participant_count__sum']
assert total is not None, "Sum returned None"
print(f"Total participants across all visits: {total}")
```

---

## Navigation & Integration

- [ ] Participant input visible in Core Details when creating AND editing visit logs
- [ ] Participant input hidden for Admin-type tasks (not applicable but shouldn't crash)
- [ ] Litter number inputs work in both create and edit modes
- [ ] Weeding and Planting +/- buttons still work (unaffected)
- [ ] Dashboard Participants card renders correctly on mobile (single-column layout)

---

## Sign-Off

| Role | Name | Date | Result |
|------|------|------|--------|
| Dev |      |      |        |
| PO  |      |      |        |
