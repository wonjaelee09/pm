# Frontend Codebase

This is a Next.js 16.1.6 (App Router) application implementing a single-page Kanban board. It is a pure frontend demo with no backend — all state is in-memory. Future parts of the project will wire it to a FastAPI backend and add auth and AI features.

## Stack

| Concern | Library / Version |
|---|---|
| Framework | Next.js 16.1.6 (App Router) |
| React | 19.2.3 |
| TypeScript | 5.x (strict mode) |
| Styling | Tailwind CSS v4 + CSS custom properties |
| Drag and drop | @dnd-kit/core ^6, @dnd-kit/sortable ^10 |
| Unit tests | Vitest 3.x + React Testing Library + jsdom |
| E2E tests | Playwright 1.58 (Chromium only) |
| Font | Space Grotesk (display), Manrope (body) via next/font/google |

## Directory Structure

```
frontend/
├── src/
│   ├── app/
│   │   ├── layout.tsx          # Root layout: font setup, metadata
│   │   ├── page.tsx            # Home page: renders <KanbanBoard />
│   │   └── globals.css         # Tailwind init + CSS design tokens
│   ├── components/
│   │   ├── KanbanBoard.tsx     # Root client component; owns all state
│   │   ├── KanbanBoard.test.tsx
│   │   ├── KanbanColumn.tsx    # Droppable column; editable title
│   │   ├── KanbanCard.tsx      # Draggable card; delete button
│   │   ├── KanbanCardPreview.tsx  # Overlay shown during drag
│   │   └── NewCardForm.tsx     # Toggle form for adding a card
│   ├── lib/
│   │   ├── kanban.ts           # Types, moveCard(), initialData
│   │   └── kanban.test.ts      # Unit tests for moveCard()
│   └── test/
│       ├── setup.ts            # Imports @testing-library/jest-dom
│       └── vitest.d.ts         # Type shims for Vitest globals
├── tests/
│   └── kanban.spec.ts          # Playwright E2E tests
├── next.config.ts              # Minimal Next.js config (no custom options yet)
├── vitest.config.ts            # jsdom env, globals: true, @ alias
├── playwright.config.ts        # baseURL: 127.0.0.1:3000, webServer: next dev
├── tsconfig.json               # strict, bundler resolution, @/* alias
├── postcss.config.mjs          # @tailwindcss/postcss plugin
└── package.json
```

## Types and Core Logic — `src/lib/kanban.ts`

```ts
type Card = {
  id: string;
  title: string;
  details: string;
};

type Column = {
  id: string;
  title: string;
  cardIds: string[];  // ordered list of card IDs
};

type BoardData = {
  columns: Column[];
  cards: Record<string, Card>;  // keyed by card ID
};
```

`moveCard(board, activeId, overId)` handles two cases:
- **Same column**: reorders `cardIds` using `arrayMove` from @dnd-kit/sortable
- **Different column**: removes `activeId` from source column, inserts it at the correct position in destination column (before `overId` if `overId` is a card, or appends if `overId` is a column ID)

`initialData` contains 5 columns (Backlog, Discovery, In Progress, Review, Done) and 8 sample cards.

## Component Details

### `KanbanBoard.tsx`
- `"use client"` — client component
- Owns the entire board in `useState<BoardData>`
- Tracks `activeCardId` during drag for the `DragOverlay`
- Uses `DndContext` (PointerSensor, 6px activation threshold, closestCorners collision)
- Event handlers: `handleDragStart`, `handleDragEnd`, `handleRenameColumn`, `handleAddCard`, `handleDeleteCard`
- Renders decorative gradient blobs, a header with column badges, and a 5-column CSS grid (`lg:grid-cols-5`)

### `KanbanColumn.tsx`
- `useDroppable({ id: column.id })` makes it a drop target
- `SortableContext` + `verticalListSortingStrategy` wraps the card list
- Editable title via an `<input>` calling `onRename` on every keystroke
- Shows a yellow ring highlight when a card is being dragged over it
- Renders `<NewCardForm>` at the bottom

### `KanbanCard.tsx`
- `useSortable({ id: card.id })` makes it draggable
- Applies `CSS.Transform.toString(transform)` as inline style for smooth movement
- Drops opacity to 0.6 and increases shadow while being dragged (`isDragging`)
- "Remove" button calls `onDelete`

### `KanbanCardPreview.tsx`
- Lightweight read-only card used inside `DragOverlay`
- Same visual as `KanbanCard` but without drag hooks or delete button
- Stronger shadow to float visually above the board

### `NewCardForm.tsx`
- Toggles between a dashed "Add a card" button and an inline form
- Form fields: title (required), details (optional textarea, 3 rows)
- On submit: trims values, validates title is non-empty, calls `onAdd`, resets and closes

## Styling

Design tokens are CSS custom properties defined in `globals.css` and mapped to Tailwind:

| Token | Value | Use |
|---|---|---|
| `--accent-yellow` | `#ecad0a` | Highlights, column indicators |
| `--primary-blue` | `#209dd7` | Links, borders, focus rings |
| `--secondary-purple` | `#753991` | Submit buttons, key actions |
| `--navy-dark` | `#032147` | Main headings |
| `--gray-text` | `#888888` | Labels, supporting text |
| `--surface` | `#f7f8fb` | Page background |
| `--surface-strong` | `#ffffff` | Card and column backgrounds |

Tailwind v4 is initialized with `@import "tailwindcss"` and extended via `@theme inline` in `globals.css`. No separate `tailwind.config.js` file.

## State Management

All board state lives in `KanbanBoard`. Children receive data and callbacks via props — no Context, no Zustand, no Redux. The pattern is:

```
KanbanBoard (state owner)
  └── KanbanColumn (onRename, onAddCard, onDeleteCard)
        └── KanbanCard (onDelete)
        └── NewCardForm (onAdd)
```

## Scripts

```
npm run dev           # Start dev server on port 3000
npm run build         # Produce static export to out/ (once output: 'export' is added)
npm run test:unit     # Run Vitest once
npm run test:unit:watch  # Run Vitest in watch mode
npm run test:e2e      # Run Playwright (starts dev server automatically)
npm run test:all      # Unit + E2E
```

## Tests

**Unit tests** use Vitest with jsdom. Located next to source files (`*.test.ts(x)`).
- `src/lib/kanban.test.ts` — 3 tests for `moveCard()` (same-column, cross-column, drop-on-column)
- `src/components/KanbanBoard.test.tsx` — 3 tests (renders columns, renames column, add + delete card)

**E2E tests** use Playwright (Chromium only, baseURL `http://127.0.0.1:3000`).
- `tests/kanban.spec.ts` — 3 tests (loads board, adds card, moves card via drag)
- Playwright starts `next dev` automatically via `webServer` config

## What Will Change in Later Parts

| Part | Change |
|---|---|
| Part 3 | Add `output: 'export'` to `next.config.ts` for Docker static build |
| Part 4 | Add `/login` page; root page checks auth and redirects |
| Part 7 | `KanbanBoard` fetches board from `GET /api/board` and persists changes via `PUT /api/board` |
| Part 10 | Add `ChatSidebar` component; board state refreshes on AI mutations |
