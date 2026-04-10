# DESIGN.md

## 0. Source Inspiration
- This design system follows the `DESIGN.md` workflow described by [VoltAgent/awesome-design-md](https://github.com/VoltAgent/awesome-design-md).
- Primary inspiration blend:
  - `VoltAgent`: void-black engineering canvas, signal-green accents, terminal-native confidence
  - `RunwayML`: cinematic media presentation, editorial section rhythm, image-led storytelling
  - `Pinterest`: masonry-style visual discovery grid for search results
- Project fit:
  - This is not a generic dashboard.
  - It is a semantic image retrieval interface where images are the hero, search is central, and system diagnostics stay secondary.

## 1. Visual Theme & Atmosphere
- **Mood**: cinematic, technical, focused, image-first
- **Design Philosophy**: blend a dark engineering surface with gallery-like visual presentation so the UI feels like a retrieval lab instead of a CRUD tool
- **Experience Goal**: the search box should feel like the command center, while result images feel like curated frames pulled from a visual archive
- **Density**: medium density; the shell is clean and spacious, but result areas may become information-rich
- **Emotional Tone**: confident, precise, slightly dramatic, never playful or toy-like

## 2. Color Palette & Roles

### Primary
- **Midnight Canvas**: `#06070A`
  - main app background
- **Graphite Surface**: `#11141A`
  - cards, tool panels, modals
- **Signal Emerald**: `#19D38A`
  - primary action, active borders, highlights, selected states
- **Search Amber**: `#F5B942`
  - query emphasis, hover accents, key callouts

### Secondary
- **Deep Teal**: `#10353A`
  - subtle background tint behind metrics and system panels
- **Steel Blue**: `#7C93B6`
  - secondary metadata accents, chart or evaluation labels
- **Cinder Border**: `#2A313C`
  - card outlines, separators, inactive controls

### Text
- **Cloud White**: `#F5F7FB`
  - main text on dark surfaces
- **Mist Gray**: `#B7C0CC`
  - secondary text and captions
- **Dim Slate**: `#7E8794`
  - tertiary metadata, quiet labels

### Status
- **Success Green**: `#22C55E`
  - success states
- **Warning Gold**: `#F59E0B`
  - caution and partial completion
- **Error Coral**: `#F87171`
  - failure states

### Background Treatments
- **Hero Gradient**: `radial-gradient(circle at top, rgba(25, 211, 138, 0.18), transparent 42%), linear-gradient(180deg, #0A0D12 0%, #06070A 100%)`
- **Panel Glow**: `linear-gradient(135deg, rgba(25, 211, 138, 0.10), rgba(124, 147, 182, 0.06))`

## 3. Typography Rules

### Font Family
- **Headings**: `Sora`, `Avenir Next`, `Segoe UI`, `sans-serif`
- **Body / UI**: `Manrope`, `Inter var`, `Segoe UI`, `sans-serif`
- **Code / Technical Labels**: `IBM Plex Mono`, `SFMono-Regular`, `Menlo`, `monospace`

### Hierarchy
| Role | Font | Size | Weight | Line Height | Letter Spacing | Notes |
|------|------|------|--------|-------------|----------------|-------|
| Hero Title | Sora | 56px | 600 | 1.02 | -1.2px | search-page impact headline |
| Page Title | Sora | 36px | 600 | 1.08 | -0.8px | major section titles |
| Section Title | Sora | 24px | 600 | 1.15 | -0.4px | result groups, panels |
| Card Title | Sora | 18px | 600 | 1.25 | -0.2px | image or result cards |
| Body Large | Manrope | 18px | 500 | 1.55 | normal | supporting explanatory text |
| Body | Manrope | 15px | 400 | 1.6 | normal | standard UI content |
| Label | Manrope | 13px | 600 | 1.45 | 0.08em | uppercase or compact labels |
| Meta | Manrope | 12px | 500 | 1.4 | 0.04em | scores, timestamps, file info |
| Code | IBM Plex Mono | 13px | 400 | 1.55 | normal | prompts, IDs, debug output |

### Principles
- Headlines should feel deliberate and compressed, not airy.
- Supporting text should remain highly legible and softer than the visual content.
- Technical data such as similarity scores, model names, and file paths should use monospace selectively.
- Avoid oversized blocks of explanatory copy on the main search surface.

## 4. Component Stylings

### Search Input
- Large, centered, command-like input with generous horizontal padding
- Background: `rgba(17, 20, 26, 0.92)`
- Border: `1px solid #2A313C`
- Focus: emerald outer ring plus subtle amber inner glow
- Shape: 18px radius, not pill-shaped
- Include quiet helper text below rather than crowded placeholder copy

### Primary Button
- Background: `#19D38A`
- Text: `#04110B`
- Weight: 700
- Radius: 14px
- Hover: slightly brighter green and 2px upward lift

### Secondary Button
- Background: transparent
- Text: `#F5F7FB`
- Border: `1px solid #2A313C`
- Hover: graphite fill with emerald border emphasis

### Result Cards
- Background: `#11141A`
- Border: `1px solid #2A313C`
- Radius: 18px
- Image corners: 16px
- Hover: slight raise, stronger border, faint emerald edge glow
- Content layout:
  - image first
  - caption snippet second
  - metadata row last

### Diagnostic Panels
- Use denser layout than result cards
- Background should blend deep teal tint with graphite base
- Good for:
  - index status
  - model configuration
  - retrieval metrics
  - evaluation summaries

### Tags and Chips
- Rounded rectangles, 999px radius is acceptable only for compact chips
- Use muted dark backgrounds with light text
- Accent chip examples:
  - query terms in amber
  - active model tags in emerald

### Empty States
- Do not use cartoon illustrations
- Use a strong sentence, one secondary explanation, and one clear action
- Prefer minimal diagram lines or subtle image placeholders

## 5. Layout Principles

### Spacing System
- Base unit: 4px
- Common scale: `4, 8, 12, 16, 24, 32, 48, 64, 80`

### Page Structure
- **Hero/Search Zone**:
  - centered title, supporting sentence, dominant search bar
- **Result Zone**:
  - masonry or staggered responsive grid with image-led cards
- **System Zone**:
  - compact side panel or lower panel for indexing status, model info, and logs

### Grid Philosophy
- Desktop:
  - 12-column base grid
  - results should feel gallery-like, not rigid dashboard tiles
- Mobile:
  - single-column results or 2-column visual grid when images allow

### Whitespace Philosophy
- Preserve large breathing room around the search area
- Let images create visual density; avoid filling empty space with extra chrome
- Technical detail should appear only when useful, not by default

## 6. Depth & Elevation
- Use layered surfaces rather than heavy shadows
- Preferred effects:
  - thin borders
  - subtle inner highlights
  - restrained outer glow for active states
- Shadow examples:
  - base card: `0 14px 40px rgba(0, 0, 0, 0.28)`
  - raised card: `0 18px 54px rgba(0, 0, 0, 0.34)`
- Avoid bright neon bloom across large areas; glow should be precise and controlled

## 7. Do's and Don'ts

### Do
- Keep the result imagery as the main visual anchor
- Use dark surfaces with selective emerald and amber accents
- Make the search experience feel premium and intentional
- Let cards vary slightly in height to support masonry-style discovery layouts
- Present technical metadata in clean, quiet sublayers
- Use motion to reinforce hierarchy, not to decorate every element

### Don't
- Don't turn the app into a generic analytics dashboard
- Don't bury the image results under large control panels
- Don't use purple as the main accent
- Don't use flat white backgrounds for the main search experience
- Don't overuse glassmorphism or blur until readability drops
- Don't mix too many accent colors at once
- Don't make every component pill-shaped

## 8. Responsive Behavior
- **Mobile**:
  - hero text scales down sharply
  - search bar becomes full-width
  - result cards stack vertically
  - system diagnostics collapse into accordions
- **Tablet**:
  - 2-column result layout
  - side metadata panels may drop below the result grid
- **Desktop**:
  - expansive centered hero
  - 3 to 5 result columns depending on card width
  - optional right-side utility panel for logs or evaluation summaries

## 9. Motion & Interaction
- Hero content may fade and rise in on first load
- Result cards should reveal with staggered entrance under 300ms
- Hover motion should be subtle:
  - small translateY
  - border brightening
  - shadow deepening
- Search submit should feel immediate; avoid long ornamental animation

## 10. Agent Prompt Guide
- "Use this `DESIGN.md` as the primary UI reference for all frontend work."
- "Build the interface as a hybrid of an AI retrieval lab and a cinematic image discovery surface."
- "Keep the search bar dominant, the images central, and the technical diagnostics secondary."
- "Use emerald for action, amber for query emphasis, and keep the rest of the palette dark and restrained."
- "Prefer masonry-style result presentation over uniform dashboard cards."
