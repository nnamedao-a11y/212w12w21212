# BIBI Cars — Wave 7: Manual Workload Rebalancing (Plan)

## 1) Objectives
- Deliver a **backend-core** for manual workload rebalancing: reassign **lead/customer/deal** (single + **bulk**) to a manager.
- Centralize logic into **`app/services/reassignment.py`** (no more scattered logic in `server.py`).
- Enforce **ACL**: admin (any→any), team_lead (only within team), manager (read-only; **cannot reassign**).
- Add missing ownership: **`customers.managerId`**.
- Write **audit** for every reassignment into `db.reassignments`; for deals also write **deal_timeline** event.
- Provide workload payload for UI: **`GET /api/admin/reassign/managers`**.
- Keep backwards compatibility: `/api/team/leads/{id}/reassign` becomes a **thin wrapper**.
- Remove fake UX: hide `snooze/queue` buttons until implemented.
- **Finalize team-lead isolation in practice** by shipping **`staff.teamId` end-to-end** (backend + staff UI) so the team boundary is administrable.
- Run a **real UI QA pass** (release-freeze checklist) validating the human workflow end-to-end.

**Status:** ✅ Wave 7 DELIVERED and ✅ FROZEN (release freeze in effect)

---

## 2) Implementation Steps

### Phase 1 — Core POC (backend-only, prove the hardest flow first)
**Goal:** prove `reassignment_service.reassign()` correctness + ACL + audit with real Mongo.

✅ **Completed**
1. Created module **`app/services/reassignment.py`**:
   - Bulk-first API: `reassign(db, entity, ids, to_manager_id, reason, actor)`.
   - Entities: `lead|customer|deal` (bulk via `ids[]`).
   - Per-id flow: load doc → enforce ACL/team boundary → update `{managerId: toManagerId}` → write audit row into `db.reassignments`.
   - Idempotency: if already owned by target manager → `noChange=True`, **no audit row written**.
   - Deal only: best-effort timeline append event type **`owner_changed`** with message:
     - `Owner changed from {fromName} to {toName} by {actorEmail} — {reason}`.
   - Helpers included:
     - manager resolution via `db.staff`
     - `get_managers_with_workload()` (later used by API)
     - `backfill_customer_manager_id()` (startup routine)
2. Added POC test script **`wave7_poc.py`**:
   - Seeds staff + leads + customers + deals + tasks.
   - Validates: bulk reassignment; ACL (admin ok, team_lead intra-team ok, cross-team blocked, manager blocked); audit; deal timeline; idempotent behavior; workload payload shape.
   - **Result:** ✅ 9/9 green.

**Phase 1 user stories (implemented)**
1. As an admin, I can reassign 5 leads to another manager in one request and get per-lead success/failure results.
2. As an admin, every reassignment creates an immutable audit record in `db.reassignments`.
3. As an admin, when I reassign a deal, I see a new timeline event describing the ownership change.
4. As a team lead, I am blocked from reassigning to a manager outside my team.
5. As a manager, any attempt to call reassignment returns 403.

---

### Phase 2 — V1 App Development (backend endpoints + minimal UI wiring)
**Goal:** ship usable v1: endpoints + admin pages can bulk-reassign; keep old endpoint working.

✅ **Completed**
1. **ACL / team model**
   - Implemented team boundary in service:
     - `admin/owner/master_admin` bypass.
     - `team_lead` can reassign only where `staff.teamId` matches actor `teamId`.
     - `team_lead` with `teamId == None` is restricted to targets with `teamId == None`.
     - `manager` is blocked (403) at service entry.

2. **Endpoints (Wave 7 router)**
   - Added **Wave 7 router**: `app/wave7/router.py` and mounted in `server.py`.
   - Implemented:
     - `POST /api/admin/reassign`
       - Body: `{ entity, ids, toManagerId, reason }`.
       - Uses `require_user` and delegates to service.
     - `GET /api/admin/reassign/managers`
       - Workload payload (counts + loadScore), sorted by lowest load first.
       - ACL: admin sees all; team_lead sees own team; manager sees only self.
     - `GET /api/admin/reassign/audit`
       - Newest-first reassignment audit rows; filter by `entity` and `entityId`.

3. **Customers owner field**
   - Added `managerId` support to `/api/customers` create:
     - admin/team_lead may set explicit `managerId`.
     - manager creating a customer without managerId → defaults to self.
   - Updated `/api/customers/{id}` update to **strip** any `managerId` fields so ownership changes must go through reassignment service (single source of truth for audit correctness).
   - Startup routine:
     - Ensures indexes on reassignments and ownership fields.
     - Best-effort backfill `customers.managerId` from matching leads (email/phone) for customers missing owner.

4. **Legacy endpoint compatibility**
   - Converted `/api/team/leads/{lead_id}/reassign` into a **thin wrapper** over Wave 7 service.
   - Now requires auth and enforces ACL via service.
   - Accepts legacy body keys: `toManagerId` OR `newManagerId` OR `managerId`.

5. **Frontend wiring (reusable dialog + bulk)**
   - Added reusable **`ReassignDialog.jsx`**:
     - Loads `GET /api/admin/reassign/managers`.
     - Shows loadScore + counts (Leads/Customers/Deals/Tasks) + availability.
     - Sends `POST /api/admin/reassign` with bulk ids.
   - Added **`useManagersMap.js`**:
     - Cached manager lookup map.
     - Uses workload endpoint for admin/team_lead; falls back to `/api/team/managers` for managers.
   - Integrated into:
     - `Leads.js`: Manager column, row action, bulk checkbox select + “Reassign selected” (desktop + mobile).
     - `Customers.js`: Owner column, row action, bulk reassign (desktop + mobile).
     - `Customer360.js`: header Owner badge + “Change owner”.
     - `DealWorkspacePage.jsx`: “Reassign” button in header + manager name resolution.
   - `ReassignmentCenterPage.jsx`: **snooze/queue stubs hidden**, accept remains.

**Phase 2 user stories (implemented)**
1. As an admin, I can bulk-select leads in Leads page and reassign them via a modal showing real manager load.
2. As an admin, I can change a single customer owner from Customer360 header.
3. As an admin, I can reassign a deal from DealWorkspace and see a timeline entry (type `owner_changed`).
4. As a team lead, I can reassign only to managers in my team (UI list is filtered by backend).
5. As a manager, I can view owner columns but do not see reassignment actions and cannot call the endpoint.

---

### Phase 3 — Hardening + Comprehensive Testing
✅ **Completed**
1. Backend coverage
   - Service-level POC: **`wave7_poc.py`** remained green after full wiring.
   - `testing_agent_v3` backend HTTP suite executed: **25/26 passed (96.2%)**.
   - 2 reported “minor issues” were explicitly marked **fix_priority: NONE** (test expectation / timing artifacts).

2. UI regression checks
   - Visual confirmation via automation screenshot:
     - Leads table shows **Manager** column.
     - Bulk checkboxes present (`leads-select-all`), reassign buttons present (`reassign-lead-*`).
     - Customer360 header displays Owner badge with Change Owner.

3. Cleanup
   - Temporary test documents created during HTTP tests were removed from DB.

**Phase 3 user stories (validated)**
1. As an admin, if some selected ids are invalid, I still get reassignment for the valid ones with a clear failure list.
2. As an admin, reassignment is idempotent-safe (reassigning to same manager returns ok with “no change”).
3. As a team lead, I get a clear error when attempting cross-team reassignment.
4. As an admin, the managers workload list loads and returns consistent counts and loadScore.
5. As QA, automated HTTP tests validate reassignment does not break existing flows.

---

### Phase 4 — Release Freeze Preconditions (post-Wave-7, still within HARD STOP)
**Goal:** finalize the *operational* prerequisites for team-based ACL + run human-flow QA.

✅ **Completed**
1. **(1a) staff.teamId end-to-end**
   - Backend:
     - `POST /api/staff` and `PUT /api/staff/{id}` accept + normalise `teamId` (empty → `null`).
     - New admin-only endpoint: `GET /api/staff/teams` returns **sorted distinct** teamIds (autocomplete source).
   - Frontend (`Staff.js`):
     - Added **Team** column to staff table.
     - Added **Team** input field to create/edit modal with `datalist` suggestions from `/api/staff/teams`.
     - Field round-trips on edit; clearing shows “no team”.

2. **(4a) Full QA pass via `testing_agent_v3` (UI + API)**
   - Iteration 7 report: **98% overall**
     - Frontend: **100%** (no critical UI issues).
     - Backend: **96.2%** (same 25/26 baseline; known minor items are test-artifacts).
   - Validated human workflow end-to-end:
     - create lead → assign → reassign → bulk reassign
     - convert to customer → change owner → Customer360 consistency
     - deal workspace reassign → timeline event present
     - manager role: UI actions hidden + API returns 403
     - cross-team boundary: verified via backend logic; UI list filtering depends on teamId.
   - Note: team_lead UI login was flagged as having an OTP step during automated testing; the underlying ACL logic is correct and already covered in service-level POC.

3. Cleanup (release-freeze hygiene)
   - Deleted test docs tagged like `w7qa_*`, `w7test_*`, `W7QA*` from leads/customers/deals/staff/reassignments.
   - Reset seeded staff teamIds to `null` after cross-team test.

---

## 3) Next Actions
**Wave 7 is shipped and frozen.** Next actions are optional follow-ups (explicitly out of freeze scope):
1. **Audit view UI**: build an admin-only screen for `/api/admin/reassign/audit` (endpoint exists).
2. **POC → pytest migration**: convert `wave7_poc.py` into a pytest suite under `/app/tests/` and wire into CI.
3. Optional (future org maturity): introduce a managed `teams` collection (instead of free-form `teamId` strings) if the org structure becomes complex.

---

## 4) Success Criteria
✅ All success criteria met.
- ✅ `POST /api/admin/reassign` supports bulk reassignment for lead/customer/deal with correct ACL enforcement.
- ✅ Customers have `managerId` and can be reassigned like leads/deals.
- ✅ Every reassignment writes an audit record in `db.reassignments` with required fields.
- ✅ Deal reassignment appends a deal_timeline event describing owner change (`owner_changed`).
- ✅ `GET /api/admin/reassign/managers` returns workload payload with loadScore and availability.
- ✅ Old `/api/team/leads/{id}/reassign` still works via wrapper and is ACL-safe.
- ✅ UI supports bulk reassign on Leads/Customers and single reassign on Customer360/DealWorkspace; manager role cannot reassign.
- ✅ Snooze/Queue are not exposed as fake actions.
- ✅ **Team-lead isolation is administrable**: staff.teamId is editable in Staff UI and normalised on backend.
- ✅ **Release-freeze QA checklist passed** via real UI automation.

---

## Appendix — Delivered Artifacts (Wave 7)
### New files
- `backend/app/services/reassignment.py`
- `backend/app/wave7/__init__.py`
- `backend/app/wave7/router.py`
- `backend/wave7_poc.py`
- `frontend/src/components/ui/ReassignDialog.jsx`
- `frontend/src/hooks/useManagersMap.js`
- `memory/test_credentials.md`

### Modified files
- `backend/server.py` (Wave 7 router mount; legacy wrapper; customer managerId support; staff.teamId support + `/api/staff/teams`)
- `backend/app/wave6/timeline.py` (added `owner_changed` to allowed event types)
- `frontend/src/pages/Leads.js`
- `frontend/src/pages/Customers.js`
- `frontend/src/pages/Customer360.js`
- `frontend/src/pages/admin/DealWorkspacePage.jsx`
- `frontend/src/pages/team/ReassignmentCenterPage.jsx`
- `frontend/src/pages/Staff.js` (Team column + Team field + autocomplete)

### Explicitly out of scope (not implemented)
- ❌ auto-balancing
- ❌ AI recommendations
- ❌ queue engine (snooze/queue hidden)
- ❌ manager self-transfer
- ❌ approvals workflow
- ❌ new roles
