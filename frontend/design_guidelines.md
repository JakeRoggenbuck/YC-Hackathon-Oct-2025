# Recompile API Error Finding Form - Design Guidelines

## Design Approach

**Selected Approach:** Design System + Technical Reference  
**Primary References:** Linear (clean developer UX), GitHub (technical authenticity), Vercel (modern dev tools)  
**Justification:** Developer-focused utility application requiring clarity, precision, and technical credibility

## Core Design Principles

1. **Technical Authenticity:** Interface should feel native to developer workflows
2. **Precision Over Decoration:** Every element serves a functional purpose
3. **Progressive Disclosure:** Show validation states and technical details contextually
4. **Frictionless Input:** Minimize cognitive load for form completion

## Typography System

**Primary Font:** Inter (clean, modern sans-serif via Google Fonts)  
**Monospace Font:** JetBrains Mono or Fira Code for technical elements

**Hierarchy:**
- Page Title: text-4xl font-bold (tracking-tight)
- Form Labels: text-sm font-medium (slightly elevated letter-spacing)
- Input Text: text-base (monospace for URLs)
- Helper Text: text-xs (regular weight)
- Validation Messages: text-sm font-medium

## Layout System

**Spacing Primitives:** Tailwind units of 2, 4, 6, and 8  
- Micro spacing: p-2, gap-2
- Standard spacing: p-4, mb-4, gap-4
- Section spacing: p-6, mb-6, py-8
- Large spacing: p-8, mt-8

**Container Structure:**
- Centered form container: max-w-md (28rem) for optimal form width
- Page padding: px-4 on mobile, px-6 on desktop
- Vertical rhythm: space-y-6 between form sections

## Component Library

### Form Container
- Single-column centered layout
- Card-style elevation with subtle border treatment
- Rounded corners (rounded-lg)
- Internal padding: p-8
- Floating above page with minimal shadow

### Input Fields
**Base Structure:**
- Label above input (mb-2)
- Full-width inputs (w-full)
- Height: h-12 for comfortable touch targets
- Padding: px-4 py-3
- Border: border-2 for emphasis on focused state
- Rounded: rounded-md
- Monospace font for URL inputs

**States:**
- Default: subtle border
- Focus: prominent border, remove outline ring, subtle glow
- Error: distinct border treatment, icon indicator
- Success: checkmark icon, success border (for valid URLs)
- Disabled: reduced opacity (opacity-50)

### Validation Feedback
**Real-time Indicators:**
- Inline icons positioned absolutely within input (right side)
- Success: checkmark icon (16px, positioned right-3)
- Error: X or alert icon
- Loading: spinner for async validation

**Helper Text:**
- Positioned below input (mt-1)
- Error messages: prominent with icon prefix
- Helper text: muted, informative
- Character count or format hints for technical fields

### Labels
- font-medium, text-sm
- Required asterisk (*) in distinct treatment
- Optional tag in muted, smaller text
- Positioned mb-2 from input

### Submit Button
- Full-width (w-full)
- Height: h-12 for consistency with inputs
- Rounded: rounded-md
- Font: text-base font-semibold
- Distinct visual weight
- Disabled state when form invalid (opacity-50, cursor-not-allowed)
- Loading state with spinner icon

### Technical Details Panel (Optional Context)
- Small card above form (mb-6)
- Monospace font
- Display: API endpoint status, rate limits, or Error Finding metrics
- Padding: p-4
- Subtle border treatment

## Page Layout Structure

**Single-Page Application:**

1. **Header Section** (py-8, text-center)
   - Recompile wordmark/logo (h-8)
   - Tagline: "API Stress Testing & Error Finding" (text-sm, muted)

2. **Main Form Section** (flex-1, flex items-center justify-center)
   - Centered vertically and horizontally
   - Form title: "Start Error Finding" (text-3xl font-bold, mb-2)
   - Subtitle: Brief description of what happens after submission (text-sm, muted, mb-8)

3. **Form Fields** (space-y-6)
   - Email input with validation
   - API URL input with format validation
   - GitHub URL (optional) with validation
   - Submit button

4. **Footer** (py-4, text-center, text-xs, muted)
   - Links: Documentation, Status Page, GitHub
   - Separated by middot (·) character

## Interaction Patterns

### Form Validation Flow
1. **On Blur:** Validate individual fields
2. **Real-time URL Validation:** Check format as user types (debounced 300ms)
3. **Submit Disabled:** Until all required fields valid
4. **Success State:** Replace form with confirmation message and next steps

### Visual Feedback
- Input focus: smooth border transition (transition-colors duration-200)
- Button hover: subtle scale or opacity shift (transform scale-105)
- Error shake: subtle horizontal shake animation on validation fail
- Success: fade-in checkmark with scale animation

### Success Screen
After submission:
- Fade out form
- Fade in success message with large checkmark icon
- Display: "Testing request submitted" heading
- Show: Summary of submitted data (email obscured, URLs displayed)
- CTA: "Submit another" button to reset form

## Accessibility Standards

- All inputs have associated labels (label htmlFor)
- ARIA attributes for validation states (aria-invalid, aria-describedby)
- Focus visible indicators
- Keyboard navigation support (tab order logical)
- Error messages announced to screen readers
- Sufficient contrast ratios throughout

## Technical Aesthetic Elements

**Monospace Touches:**
- URLs displayed in monospace
- API endpoint format hints in monospace
- Success screen data summary in monospace

**Developer Indicators:**
- Subtle grid background pattern (optional)
- Terminal-style cursor in focused inputs
- HTTP status code references in helper text
- Technical terminology in microcopy

**No Animations Except:**
- Input focus transitions
- Validation state changes
- Success screen transition
- Button hover states (subtle)

## Responsive Behavior

**Mobile (<768px):**
- Container: px-4
- Form padding: p-6 (reduced from p-8)
- Title: text-3xl (from text-4xl)
- Maintain full-width inputs

**Desktop (≥768px):**
- Container: max-w-md centered
- Full spacing as specified
- Comfortable white space around form

## Images

**No hero images required.** This is a utility form application focused on function over visual storytelling. The technical aesthetic is achieved through typography, layout precision, and interaction design rather than imagery.