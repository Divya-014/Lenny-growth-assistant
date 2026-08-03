# Design Specification Document

## Project: Lenny Growth Assistant

This document details the visual layouts, UI decisions, CSS design tokens, and viewport specifications for the frontend workspace.

---

## 1. Brand Persona & Visual Theme
The interface employs a **Vercel/Linear-inspired dark workspace theme**. It is built on top of a highly refined HSL slate palette with vibrant indigo primary accents and emerald secondary signals representing metrics and active statuses.

*   **Primary Background:** Deep Slate (`#020617` / `bg-slate-950`)
*   **Surface Cards:** Translucent Slate (`rgba(15, 23, 42, 0.6)` / `bg-slate-900/60`)
*   **Accents:** Indigo (`#4f46e5` / `bg-indigo-600`) and Emerald (`#34d399` / `text-emerald-400`)
*   **Borders:** Subtle border lines (`border-slate-800/80` or `border-slate-900`)
*   **Typography:** Google Font **Inter** (300 to 800 weights) loaded dynamically.

---

## 2. Page Layout Structure

```text
+-----------------------------------------------------------------------------+
|                                  TOP NAVBAR                                 |
| [Logo] Lenny Growth      [Active Status]       [OpenAI] [Anthropic] [Ollama]|
+------------+-----------------------------------+----------------------------+
|            |                                   |                            |
|  SIDEBAR   |            CHAT FEED              |      ARTIFACT VIEWER       |
|            |                                   |                            |
| [New Chat] | User: "Write Ship30 Loop essay"   | +------------------------+ |
|            |                                   | | PREVIEW | CODE | [Down]| |
| History:   | Assistant: "Generating loop..."   | +------------------------+ |
| - Loop comparative                             | |                        | |
| - AARRR SaaS                                   | | Renders sandboxed HTML | |
|            | +-------------------------------+ | | iframe or markdown document| |
|            | | Chat Input box           [S]  | | |                        | |
|            | +-------------------------------+ | |                        | |
+------------+-----------------------------------+----------------------------+
```

---

## 3. Component Details & UI Decisions

### 3.1 Left Panel: Chat Dashboard
*   **Sidebar (Width: `w-64`):**
    *   Holds the **New Chat** trigger, the **Chat History** list, and the active system status.
    *   Collapses dynamically into a zero-width container (`w-0` / `overflow-hidden`) when clicking the floating toggler button (`ChevronRight`), allowing maximum workspace real estate for coding or reading.
*   **Chat Container:**
    *   Centered feed limited to `max-w-3xl` for optimal reading width.
    *   Scrolls automatically to the bottom on incoming responses.
    *   Renders message bubbles with rounded edges (`rounded-2xl`). Assistant bubbles use transparent glass backgrounds (`glass-panel`) with thin borders.
*   **Prompt Entry Bar:**
    *   Pinned to the bottom of the feed. Includes an absolute-positioned arrow icon for submission, and a disclaimer indicating that results are strictly restricted to transcripts.

### 3.2 Right Panel: Claude-style Artifact Viewer
*   **Conditional Rendering:**
    *   The panel is hidden (`w-0` / `opacity-0` / `pointer-events-none`) by default.
    *   It expands smoothly (`w-[50%]` / `opacity-100` / `transition-all duration-300`) as soon as the parser detects code artifacts (HTML, markdown code blocks, or custom XML tags) in the last assistant response.
*   **Sandboxed HTML Preview:**
    *   Displays code inside an iframe: `<iframe srcDoc={content} sandbox="allow-scripts" />`.
    *   Keeps JavaScript execution isolated from the main website shell.
*   **Markdown Viewer:**
    *   Uses `react-markdown` with strict typography configurations (tailored fonts, list indents, margins, and code block styles).
*   **Header Tab Switcher:**
    *   Exposes a toggle button: **Preview** (renders HTML or formatted markdown) vs. **Code** (renders raw monospace source code).
    *   Exposes a **Download** button to download files locally.

---

## 4. Responsive Viewport Specifications
*   **Desktop & Laptops (`min-width: 1024px`):** Fully supports side-by-side split screen workspace views.
*   **Tablets (`min-width: 768px`):** Collapses the sidebar by default. The Chat feed and Artifact Viewer share a 50/50 split.
*   **Mobile Screens (`max-width: 640px`):** Hides the sidebar completely. If an artifact is opened, it stacks vertically or takes 100% of the viewport with a back toggle to switch to chat view.
