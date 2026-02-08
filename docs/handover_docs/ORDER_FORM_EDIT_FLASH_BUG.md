# Order Form Edit Mode Flash Bug

**Status:** Unresolved — initial fix applied but problem persists after hard refresh.

## Bug Description

When clicking "Edit" on the order detail page (`/orders/$orderId`), the input field outlines flash briefly then disappear. The form snaps back to read-only mode almost immediately, making editing impossible.

## Architecture Overview

The relevant component tree:

```
OrderReviewPage
  └─ AuthGuard
       └─ OrderReviewContent          ← owns `isEditing` state (useState)
            ├─ OrderSourcePanel       ← left panel, email/source display
            ├─ OrderDataForm          ← the form (react-hook-form)
            ├─ FormPreview            ← renders generated form preview
            └─ OrderActions           ← Edit/Save/Approve/Reject buttons
```

### Key files

| File | Role |
|------|------|
| `frontend/src/routes/orders/$orderId.tsx` | Parent page — holds `isEditing` state, passes it as props |
| `frontend/src/components/orders/OrderDataForm.tsx` | The form — uses `react-hook-form`, has `useEffect` that resets form from `order` prop |
| `frontend/src/hooks/useOrders.ts` | React Query hooks — `useOrder(id)` fetches a single order |
| `frontend/src/components/orders/OrderActions.tsx` | Action bar — has Edit/Save buttons, calls `onToggleEdit` |
| `frontend/src/components/AuthGuard.tsx` | Auth wrapper — renders children only when authenticated |
| `frontend/src/contexts/SimpleAuthContext.tsx` | Auth provider used in dev mode |

### Data flow for "Edit" click

1. User clicks "Edit" in `OrderActions` (line 88)
2. Calls `onToggleEdit` → `setIsEditing(!isEditing)` in `OrderReviewContent` (line 234)
3. `OrderReviewContent` re-renders with `isEditing = true`
4. `OrderDataForm` receives `isEditing = true` → conditionally renders `<Input>` elements instead of `<span>` elements
5. `OrderActions` receives `isEditing = true` → shows "Save Changes" instead of "Edit"

## Original Hypothesis (from plan)

The `useOrder` query had no `staleTime`, so toggling `isEditing` triggers a React re-render, which causes React Query to background-refetch the (immediately stale) order data. When the refetched `order` object arrives with a new reference, the `useEffect` in `OrderDataForm` unconditionally called `reset(getDefaults(order))`, re-rendering the form and causing the flash.

## Changes Applied

### 1. Guarded `reset()` with `!isEditing` in OrderDataForm

**File:** `frontend/src/components/orders/OrderDataForm.tsx` (lines 71-76)

```tsx
// Before
useEffect(() => {
  reset(getDefaults(order));
}, [order, reset]);

// After
useEffect(() => {
  if (!isEditing) {
    reset(getDefaults(order));
  }
}, [order, reset, isEditing]);
```

### 2. Added `staleTime` to `useOrder` query

**File:** `frontend/src/hooks/useOrders.ts` (lines 24-31)

```tsx
export function useOrder(id: string) {
  return useQuery({
    queryKey: ['order', id],
    queryFn: () => fetchOrder(id),
    enabled: !!id,
    staleTime: 30_000,  // added
  });
}
```

## Investigation Findings

We thoroughly investigated the following and **ruled them out** as causes:

### AuthGuard — Cleared

- `SimpleAuthContext` sets `loading: true` only on initial mount, then `false` after `/auth/me` resolves. Never goes back to `true`.
- AuthGuard only shows spinner during initial load. No flickering that would unmount/remount children and reset `isEditing`.

### OrderActions — Cleared

- Edit button calls `onToggleEdit` once per click. No double-fire, no effects that call it again.
- When `isEditing` is `true`, the Edit button is replaced by "Save Changes" (a `type="submit"` button tied to `form="order-data-form"`). No way to accidentally toggle back.

### Component Unmount/Remount — Cleared

- No `key` prop on `<OrderDataForm>` that could change and force a remount.
- The early returns in `OrderReviewContent` (`if (isLoading)` → Skeleton, `if (!order)` → Not Found) should not trigger during background refetches. React Query's `isLoading` is `true` only when there's no cached data AND a fetch is in progress.

### React Query `QueryClient` — Cleared

- `QueryClient` is created with no default options in `main.tsx` (line 12).
- No global `staleTime` override. No `StrictMode` wrapper.

### `handleSave` closure — Not the issue for the flash

- `handleSave` captures `order` but is only called on save, not on edit toggle.

## What Remains Unexplained

The `!isEditing` guard on the `useEffect` should logically prevent the form reset during editing. The `staleTime: 30_000` should prevent unnecessary refetches. Both changes are confirmed in the source files. A hard browser refresh was done.

**Yet the flash persists.** This suggests the root cause is **not** (or not solely) the `useEffect` reset. Possible remaining causes to investigate:

### 1. Something is resetting `isEditing` to `false`

`isEditing` lives as `useState(false)` inside `OrderReviewContent`. The only explicit `setIsEditing(false)` call is in `handleSave` (line 137). If the component unmounts and remounts for any reason, `isEditing` resets to `false`. Add a `console.log` or `useEffect` to trace `isEditing` changes:

```tsx
useEffect(() => {
  console.log('[OrderReviewContent] isEditing changed to:', isEditing);
}, [isEditing]);
```

### 2. The component may be unmounting/remounting invisibly

If something in the router or layout causes `OrderReviewContent` to unmount and remount (e.g., route re-evaluation, layout shift), all `useState` resets. Check with:

```tsx
useEffect(() => {
  console.log('[OrderReviewContent] MOUNTED');
  return () => console.log('[OrderReviewContent] UNMOUNTED');
}, []);
```

### 3. React Query delivering a new `order` reference synchronously

If React Query's structural sharing fails (e.g., the server returns slightly different JSON — timestamps, computed fields), the `order` reference changes on every refetch. While our guard should handle this, verify by logging inside the `useEffect`:

```tsx
useEffect(() => {
  console.log('[OrderDataForm] useEffect fired — isEditing:', isEditing, 'order.id:', order.id);
  if (!isEditing) {
    console.log('[OrderDataForm] Resetting form');
    reset(getDefaults(order));
  }
}, [order, reset, isEditing]);
```

### 4. Another query invalidation is triggering a cascade

`FormPreview` and `OrderSourcePanel` both make their own queries (product specs, calculations, email data) with no `staleTime`. These won't reset the form directly, but heavy re-rendering from these could interact unexpectedly. Consider memoizing `OrderDataForm` with `React.memo()`.

### 5. The `onSave` prop causes unnecessary re-renders

`handleSave` is an inline async function in `OrderReviewContent` — a new reference every render. Every time the parent re-renders (from any query update), `OrderDataForm` gets a new `onSave` prop and re-renders. While this alone shouldn't cause the flash, wrapping it in `useCallback` would eliminate it as a variable:

```tsx
const handleSave = useCallback(async (headerData, lineItems) => {
  // ... existing save logic using order from ref or queryClient
}, [order, updateOrderMutation, updateLineItemMutation]);
```

## Recommended Next Steps

1. **Add the debug console.logs** listed above (mount/unmount, isEditing changes, useEffect triggers) and reproduce the bug. The logs will reveal whether:
   - The component is unmounting/remounting (losing state)
   - `isEditing` is being set back to `false` by something unexpected
   - The `useEffect` is running with `isEditing = false` when it shouldn't be

2. **Check React DevTools Profiler** — record the edit click interaction and inspect what triggered each re-render.

3. **If the component IS remounting**, investigate the TanStack Router — route params or layout changes could cause this. Check if `Route.useParams()` returns a new `orderId` reference that triggers something upstream.

4. **If `isEditing` stays `true` but the form still flashes**, the issue may be CSS/rendering rather than state — inspect whether `disabled` attribute or conditional `isEditing ? <Input> : <span>` is flickering due to an intermediate render state.
