# Integration Tracing Reference

End-to-end tracing for code that connects to external systems (frontend ↔ backend ↔ database ↔ external APIs). Used by Step 2d of `code-review`.

## Contents

- [Frontend → Backend](#frontend--backend)
- [Backend → Database](#backend--database)
- [Backend → External APIs](#backend--external-apis)
- [What to look for](#what-to-look-for)
- [Example trace](#example-trace)

## Frontend → Backend

- Find the API endpoint being called (`fetch`, `axios`, API client)
- Locate the backend route handler
- Verify request/response contracts match
- Check error handling on both sides

```bash
# API calls in frontend
grep -r "fetch\|axios\|api\." --include="*.tsx" --include="*.ts"

# Corresponding backend route
grep -r "router\.\|app\.\(get\|post\|put\|delete\)" --include="*.ts"
```

## Backend → Database

- Trace queries to schema definitions (migrations, ORM models)
- Verify column names, types, constraints match
- Check for missing migrations for new/changed columns

## Backend → External APIs

- Verify API contracts (request/response shapes) against the provider's current spec
- Check authentication/authorization (tokens, scopes, expiry handling)
- Review timeout and retry handling
- Confirm error responses are handled (not just 2xx)

## What to Look For

1. **Contract mismatches** — Frontend expects `userId`, backend sends `user_id`
2. **Missing fields** — Backend added required field, frontend doesn't send it
3. **Type mismatches** — Frontend sends string, backend expects number
4. **Error handling gaps** — Frontend doesn't handle 4xx/5xx responses
5. **Race conditions** — Frontend assumes sync, backend is async / eventually consistent
6. **Auth/permissions** — Frontend calls endpoint user doesn't have access to
7. **Pagination mismatches** — Frontend expects array, backend returns paginated object
8. **Validation gaps** — Frontend validates, backend doesn't (or vice versa)

## Example Trace

```
Frontend: src/components/OrderForm.tsx
  → calls: POST /api/orders { productId, quantity }

Backend: src/routes/orders.ts
  → handler: createOrder(req.body)
  → validates: productId (required), quantity (number > 0)

Service: src/services/orderService.ts
  → checks: inventory, user balance
  → calls: db.orders.create()

Database: migrations/001_orders.sql
  → schema: orders(id, product_id, quantity, user_id, status)

GAPS FOUND:
- Frontend sends `quantity` as string, backend expects number
- Backend doesn't return created order, frontend expects it
- No error handling in frontend for insufficient inventory
```
