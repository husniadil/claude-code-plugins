# Gap Categories Reference

Detailed definitions for each gap category used in code review.

## 1. Business Logic

Issues where code doesn't correctly implement business requirements or domain rules.

**Severity Guidelines:**

- HIGH: Core business rule violated, financial/legal impact, data integrity at risk
- MED: Edge case not handled, workflow incomplete
- LOW: Minor business rule deviation, cosmetic issues

**What to Look For:**

- Missing validation rules (e.g., order minimum, age verification)
- Incorrect workflow transitions (e.g., allowing payment before cart validation)
- Wrong business calculations (e.g., discount logic, tax computation)
- Missing edge cases (e.g., what if quantity is 0? What if user cancels mid-flow?)
- Domain constraint violations (e.g., negative inventory, overlapping bookings)
- Incorrect state management (e.g., order marked complete before shipping)
- Missing required fields for business processes
- Timezone/locale issues in business dates

**Examples:**

```javascript
// Missing business validation
async function createOrder(cart) {
  // BUG: No check for minimum order value
  // BUG: No check if items are still in stock
  return await db.orders.create(cart);
}

// Incorrect workflow
async function processPayment(orderId) {
  await chargeCard(orderId);
  // BUG: Should verify order status before charging
  // BUG: Should check if payment already processed (idempotency)
}

// Wrong business calculation
function calculateDiscount(price, coupon) {
  return price * coupon.percentage;
  // BUG: Doesn't check if coupon is expired
  // BUG: Doesn't check minimum purchase requirement
  // BUG: Doesn't cap discount at maximum allowed
}

// Missing domain constraint
function updateInventory(productId, quantity) {
  inventory[productId] -= quantity;
  // BUG: Can go negative - should check available stock
}
```

## 2. Integration Issues

Problems where different system components don't work together correctly.

**Severity Guidelines:**

- HIGH: Data loss, corruption, or system failure at integration boundaries
- MED: Functionality broken due to contract mismatch
- LOW: Minor inconsistencies that don't break functionality

**What to Look For:**

- **Contract mismatches**: Frontend expects `userId`, backend sends `user_id`
- **Missing fields**: Backend added required field, frontend doesn't send it
- **Type mismatches**: Frontend sends string "123", backend expects number 123
- **Response shape changes**: Frontend expects array, backend returns `{ data: [], pagination: {} }`
- **Error response handling**: Frontend doesn't handle 4xx/5xx error shapes
- **Auth token issues**: Token not passed, wrong header name, expired handling
- **Pagination mismatches**: Different page size assumptions, off-by-one in page numbers
- **Validation gaps**: Frontend validates but backend doesn't (or vice versa)
- **Async/timing issues**: Frontend assumes sync response, backend is eventually consistent
- **Database schema drift**: Code references columns/tables that don't exist or have different types

**Examples:**

```javascript
// Frontend - expects camelCase
const response = await fetch('/api/user')
const { userId, userName } = await response.json()
// BUG: Backend sends { user_id, user_name }

// Frontend - doesn't handle error response
async function createOrder(data) {
  const res = await fetch('/api/orders', { method: 'POST', body: data })
  return res.json() // BUG: Doesn't check res.ok, doesn't handle error shape
}

// Backend - changed response shape
app.get('/api/products', (req, res) => {
  const products = db.products.findAll()
  res.json({ data: products, total: products.length })
  // BUG: Frontend expects array directly, not { data, total }
})

// Type mismatch
// Frontend sends:
fetch('/api/items', { body: JSON.stringify({ quantity: "5" }) })
// Backend expects:
function createItem({ quantity }: { quantity: number }) {
  // BUG: "5" !== 5, validation may fail or cause bugs
}

// Database schema mismatch
const user = await db.query('SELECT email FROM users WHERE id = ?', [id])
// BUG: Column renamed to 'email_address' in migration
```

## 3. Logic Errors

Issues with the correctness of code logic (technical bugs, not business rules).

**Severity Guidelines:**

- HIGH: Will cause incorrect behavior or data corruption
- MED: Edge case handling issues
- LOW: Suboptimal logic that still works

**What to Look For:**

- Off-by-one errors in loops or array indexing
- Incorrect boolean conditions (using `&&` instead of `||`)
- Wrong comparison operators (`<` vs `<=`)
- Null/undefined checks in wrong order
- Race conditions in async code
- Incorrect state transitions
- Missing break statements in switch cases

**Examples:**

```javascript
// Off-by-one error
for (let i = 0; i <= arr.length; i++) // Should be < not <=

// Wrong condition
if (user && user.isAdmin || user.isModerator) // Missing parentheses

// Null check order
if (obj.property && obj) // Wrong order, will throw
```

## 4. Security Issues

Vulnerabilities that could be exploited.

**Severity Guidelines:**

- HIGH: Directly exploitable (injection, auth bypass)
- MED: Requires specific conditions to exploit
- LOW: Defense-in-depth issues

**What to Look For:**

- SQL injection (string concatenation in queries)
- XSS (unescaped user input in HTML)
- Command injection (user input in shell commands)
- Path traversal (user input in file paths)
- Hardcoded credentials or API keys
- Missing authentication checks
- Insecure direct object references
- CSRF vulnerabilities
- Sensitive data in logs
- Weak cryptography

**Examples:**

```javascript
// SQL injection
db.query(`SELECT * FROM users WHERE id = ${userId}`);

// XSS
element.innerHTML = userInput;

// Hardcoded secret
const API_KEY = "sk-1234567890";
```

## 5. Performance Problems

Code that will cause slowdowns or resource issues.

**Severity Guidelines:**

- HIGH: O(n²) or worse in hot paths, memory leaks
- MED: Unnecessary work, inefficient patterns
- LOW: Minor optimizations possible

**What to Look For:**

- N+1 query patterns (queries in loops)
- Unnecessary re-renders in React
- Missing memoization for expensive computations
- Large objects in memory without cleanup
- Synchronous I/O in event loops
- Unbounded data structures
- Missing pagination for large datasets
- Inefficient regex patterns
- Excessive DOM manipulation

**Examples:**

```javascript
// N+1 queries
for (const user of users) {
  const posts = await db.query(
    `SELECT * FROM posts WHERE user_id = ${user.id}`
  );
}

// Missing memoization
function Component({ items }) {
  const sorted = items.sort(); // Sorts on every render
}
```

## 6. Error Handling

Missing or improper handling of error cases.

**Severity Guidelines:**

- HIGH: Crashes, data loss, security implications
- MED: Poor user experience, silent failures
- LOW: Missing logging, generic messages

**What to Look For:**

- Unhandled promise rejections
- Empty catch blocks
- Missing try/catch around I/O operations
- Not checking return values
- Swallowing errors silently
- Generic error messages (no context)
- Missing cleanup in error paths
- Not propagating errors appropriately

**Examples:**

```javascript
// Empty catch block
try {
  await saveData();
} catch (e) {
  // Silent failure
}

// Unhandled rejection
fetch("/api/data").then(handleData); // No .catch()

// Missing error check
const result = JSON.parse(input); // Can throw
```

## 7. Code Style

Inconsistencies with project conventions.

**Severity Guidelines:**

- HIGH: N/A (style issues are never high severity)
- MED: Significant deviation from patterns
- LOW: Minor naming or formatting issues

**What to Look For:**

- Inconsistent naming conventions (camelCase vs snake_case)
- Inconsistent formatting (handled by prettier usually)
- Magic numbers without constants
- Overly complex expressions
- Deep nesting (>3 levels)
- Long functions (>50 lines)
- Inconsistent error message formats
- Mixed async patterns (callbacks + promises)

**Examples:**

```javascript
// Magic number
if (retryCount > 3)
  if (a) {
    // Should be MAX_RETRIES

    // Deep nesting
    if (b) {
      if (c) {
        if (d) {
          // Too deep
        }
      }
    }
  }
```

## 8. Missing Tests

Code paths that should have test coverage.

**Severity Guidelines:**

- HIGH: Critical business logic untested
- MED: Common paths untested
- LOW: Edge cases untested

**What to Look For:**

- New functions without corresponding tests
- Changed logic without updated tests
- Error paths not tested
- Edge cases not covered
- Integration points untested
- Security-sensitive code untested

**Examples:**

```javascript
// New function without test
export function calculateDiscount(price, couponCode) {
  // Complex logic with no test file
}

// Changed behavior
- if (user.role === 'admin')
+ if (user.role === 'admin' || user.role === 'super_admin')
// Test should be updated to cover new case
```

## 9. Documentation Gaps

Missing or outdated documentation for complex code.

**Severity Guidelines:**

- HIGH: N/A (docs are never high severity)
- MED: Public API without docs
- LOW: Complex internal logic without comments

**What to Look For:**

- Public functions without JSDoc/docstrings
- Complex algorithms without explanation
- Non-obvious business rules without comments
- Outdated comments that don't match code
- Missing README updates for new features
- Undocumented configuration options
- Missing changelog entries

**Examples:**

```javascript
// Missing docs on public API
export function processPayment(amount, currency, metadata) {
  // Complex 50-line function with no documentation
}

// Outdated comment
// Retries 3 times
while (retryCount < 5) { // Comment says 3, code says 5
```

## Severity Decision Tree

```
Does it violate core business rules or cause financial/legal impact?
├── Yes → HIGH
└── No
    └── Does it break integration between systems (frontend/backend/DB/API)?
        ├── Yes, causes data loss or system failure → HIGH
        ├── Yes, breaks functionality → MED
        └── No
            └── Is it exploitable for security?
                ├── Yes → HIGH
                └── No
                    └── Will it cause incorrect behavior or data corruption?
                        ├── Yes → HIGH
                        └── No
                            └── Will it affect user experience or business workflow?
                                ├── Yes → MED
                                └── No → LOW
```
