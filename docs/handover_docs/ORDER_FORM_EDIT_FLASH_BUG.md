# Bug: Order Form Flash / Revert to Read-only on Edit
**Status:** RESOLVED
**Date:** 2026-02-09

## Description
When clicking the "Edit" button on the Order Review page, the form briefly enters edit mode (or not at all) and immediately reverts to read-only mode. In some cases, the component unmounts and remounts. In others, the form submits immediately.

## Root Cause Analysis
This bug had multiple contributing factors, all of which were addressed:

1.  **Skeleton Loader Race Condition:** The `OrderReviewContent` component was unmounting when `isLoading` was true during background refetches.
    *   *Fix:* Changed loading condition to `if (isLoading && !order)` to keep UI mounted during background updates.

2.  **AuthProvider Unmounting:** The `SimpleAuthProvider` in `main.tsx` was declared inside the `App` component (`const AuthProviderComponent = ...`). This caused the entire auth provider to unmount and remount on every app re-render, resetting auth state (`loading=true`), which triggered `AuthGuard` to show a spinner, unmounting the order page.
    *   *Fix:* Moved `AuthProviderComponent` logic **outside** the `App` component to ensure stable reference.

3.  **AuthGuard Loading State:** `AuthGuard` was showing a loading spinner whenever `loading` was true, even if `isAuthenticated` was already true.
    *   *Fix:* Updated `AuthGuard` to only show loading spinner if `!isAuthenticated`.

4.  **Button Replacement Event Propagation (The "Flash"):** When "Edit" was clicked, `isEditing` became true. React immediately replaced the "Edit" button with the "Save Changes" button (which acted as a submit button). The mouse click event likely propagated to the new "Save" button or form context, causing it to trigger a form submission immediately. The form submission handler (`handleSave`) ran, saved the form (no changes), and turned `isEditing` off.
    *   *Fix:*
        *   Added `key="edit-btn"` and `key="save-btn"` to `OrderActions` buttons to force React to treat them as separate DOM elements.
        *   Added `e.preventDefault()` and `e.stopPropagation()` to the "Edit" button click handler.
        *   Explicitly set `type="button"` on the "Edit" button to prevent any implicit form submission.

## Resolution
The bug is fully resolved. The edit mode now persists correctly through background refreshes, and the form does not auto-submit.

## Verification
- Validated via browser subagent that clicking "Edit" keeps the form in edit mode for >5 seconds.
- Validated that `handleSave` is NOT called upon clicking "Edit".
- Validated that unmounts do not occur during background fetches.
- Validated that `isEditing` state persists.

## Relevant Files
- `frontend/src/routes/orders/$orderId.tsx`
- `frontend/src/components/orders/OrderActions.tsx` (Key Fix)
- `frontend/src/main.tsx` (AuthProvider Fix)
- `frontend/src/components/AuthGuard.tsx` (Loading Logic Fix)
