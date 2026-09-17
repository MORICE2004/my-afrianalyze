# My AfriAnalyze Design System

## Moving Away from "Card Overuse"
The current design suffers from "card overuse" - trapping every piece of information inside a rounded rectangle with a drop shadow. This wastes space and creates visual clutter.

### New Rules for Layout & Containers
- **Not everything is a card:** Group related information using typography, whitespace, and subtle divider lines instead of explicit bounding boxes.
- **Cards are for interactive or distinct objects:** Only use cards for things that can be selected, dragged, or represent a distinct entity (like a company profile snippet).

## Core Components

### 1. Tables (The Backbone)
- Must support ultra-high density.
- Borderless rows with subtle zebra striping or hover states.
- Right-aligned numerical columns with tabular figures.
- Sticky headers for large datasets.

### 2. Side Panels / Drawers
- Use for contextual deep dives without losing the main view (e.g., clicking a company in a screener opens a side panel with quick stats instead of navigating away).
- Slide in from the right edge, full height.

### 3. Inline Metrics
- Display key metrics directly within text or headers (e.g., "Market Cap: **$4.2B**") instead of forcing them into isolated metric cards.
- Use sparklines inline to show trends without requiring a full chart component.
