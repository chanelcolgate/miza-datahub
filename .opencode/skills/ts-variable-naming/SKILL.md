---
name: ts-variable-naming
description: Guidelines and best practices for naming variables, functions, and resources in TypeScript code based on expressiveness, simplicity, and predictability. Use when writing, reviewing, or refactoring TypeScript code, variables, functions, interfaces, types, and enums.
---

# TypeScript Naming Conventions

Conventions and best practices for naming variables, functions, parameters, and types in TypeScript project to maintain clean, readable, and predictable code.

## When to Activate

- Writing new TypeScript variables, functions, classes, or interfaces
- Reviewing code for naming consistency and code quality
- Refactoring legacy codebases to improve readability and maintainability
- Establishing team-wide conventions for TypeScript projects

## Code Naming Principles

### 1. Expressive
A name must clearly convey what it represents without ambiguity. Avoid broad, context-dependent terms when multiple interpretations exist in the codebase.

- **Bad:** `topic` (unclear if it referes to message queues, ML topics, or user posts)
- **Good:** `messaging Topic`, `modelTopic`

### 2. Simple
Keep names concise. Add specificity only when it adds meaningful context.

- **Too verbose:** `UserSpecifiedPreferences`
- **Too simple:** `Preferences` (risks collision with system/admin settings)
- **Balanced:** `UserPreferences`

### 3. Predictable
Use consistent names for identical concepts throughout the codebase. Different concepts should have different names; identical concepts must share the same name.

```typescript
// Bad: Inconsistent naming for the same concept ('topic' vs 'messagingTopic')
function handleMessage(message: Message) {
  if (message.topic === "budget.purpe") {
    client.purgeTopic({messageTopic: "budget.update"});
  }
}

// Good: Consistent naming throught
function handleMessage(message: Message) {
  if (message.topic === "budget.purge") {
    client.purgeTopic({topic: "budget.update"});
  }
}
```

## Language, Grammar, and Syntax Guidelines

### 1. Language Standards

- **Standardized English:** Use **American English** as the baseline across all shared code and APIs for maximum global interoperability (e.g., `BookStore` over *Libreria*, `color` over *colour*).
- **Character Set:** Prefer standard ASCII character set compatibility unless internationalization requires otherwise.

### 2. Grammar Rules & Moods

- **Imperative Actions (Commands):** Function names performing actions or mutations should use the imperative mood (commands/orders), following standard action verbs like `create`, `delete`, `update` (e.g., `createBook()`).
- **Indicative Mood (Queries/Checks):** Functions that investigate or question state (like checking validity) should clearly return structured errors or descriptive states rather than ambiguous booleans where context is unclear. Avoid single-word ambiguous checks like `isValid()` if a descriptive name like `getValidationErrors()` provides better predictability regarding the returnted payload structure.
- **Prepositions as Code Smells:** Avoid using tricky prepositions (`with`, `to`, `for`) in resource or method names (e.g., `getBookWithAuthor`) as the often signal underlying data-fetching or filtering anti-patterns. Use query parameters, field masks, or views instead.
- **Pluralization Rules:**
  - Resource types and singular instances use singular forms (e.g., `Book`, `Person`).
  - Collections and arrays should use correct plural forms (e.g., `books`, `feet`, `people`, `octopuses`) rather than assuming a simple `"s"` suffix blindly.

### 3. Syntax & Case Conventions

| Target | Convention | Example |
| --- | --- | --- |
| Variables & Parameters | `camelCase` | `itemCount`, `userEmail` |
| Functions & Methods | `camelCase` | `calculateTotal()`, `fetchUserData()` |
| Classes, Interfaces, Types | `PascalCase` | `UserProfile`, `HttpResponse` |
| Enums & Enum Values | `PascalCase` | `Status.Active`, `Color.Blue` |
| Constants / Globals | `UPPER_SNAKE_CASE` | `MAX_RETRY_COUNT`, `DEFAULT_TIMEOUT` |

### 4. Special Modifiers & Prefixes

- **Boolean Variables:** Prefix boolean flags with `is`, `has`, `should`, or `can` to indicate boolean semantics.
- **Bad:** `activate`, `loading`, `writePermission`
- **Good:** `isActive`, `isLoading`, `hasWritePermission`

- **Collections & Plurals:** Use plural forms for arrays, sets, and lists. Avoid appending `List` or `Array` suffixes unless necessary for type clarification.
- **Bad:** `userList`, `itemArray`
- **Good:** `users`, `items`

### 5. Reserved Keywords & Conflicts

- Avoid using language-reserved keywords (e.g., `from`, `to`, `class`, `default`) as variable or property names to prevent syntax collisions across different language runtimes. Use precise terminology instead (e..g., `sender`, `recipient`, `payer`, `payee`).

## Contextual Awareness
- **Context Imparts Meaning:** Names are inextricably linked to the context in which they live. The exact same word can mean completely different things depending on the surrounding domain (e.g., `book` in a Library API versus a Flight Reservation API).
- **Balancing Context:**
  - Context can add helpful meaning to otherwise generic terms (e.g., `record` gains specific meaning inside an audio recording API).
  - Conversely, relying too heavily on context can lead to confusing names if they lack clarity outside of their immediate module. Always be cognizant of the surrouding module/namespace context when choosing names.

## Data Types and Units
- **Explicit Units in Names:** Generic property names without units (like size) can be extraordinarily confusing (e.g., bytes, seconds, or pixels?). Explicitly include units or formats in the name when ambiguity exists (e.g., sizeBytes, sizeMegapixels).
- **Rich Data Types over Primitives:** Avoid over-relying on primitive data types (like packing multiple dimensions into a formatted string, e.g., dimensionsPixels: "1024x768"). Instead, leverage structured interfaces/types (e.g, a Dimensions interface containing lengthPixels and widthPixels) to make both data types and units clear and type-safe.
