---
name: Nexus Tetouan Smart City
colors:
  surface: '#f7f9fb'
  surface-dim: '#d8dadc'
  surface-bright: '#f7f9fb'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f2f4f6'
  surface-container: '#eceef0'
  surface-container-high: '#e6e8ea'
  surface-container-highest: '#e0e3e5'
  on-surface: '#191c1e'
  on-surface-variant: '#424656'
  inverse-surface: '#2d3133'
  inverse-on-surface: '#eff1f3'
  outline: '#727687'
  outline-variant: '#c2c6d8'
  surface-tint: '#0054d6'
  primary: '#0050cb'
  on-primary: '#ffffff'
  primary-container: '#0066ff'
  on-primary-container: '#f8f7ff'
  inverse-primary: '#b3c5ff'
  secondary: '#006e2a'
  on-secondary: '#ffffff'
  secondary-container: '#5cfd80'
  on-secondary-container: '#00732c'
  tertiary: '#4b5a70'
  on-tertiary: '#ffffff'
  tertiary-container: '#63738a'
  on-tertiary-container: '#f6f8ff'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#dae1ff'
  primary-fixed-dim: '#b3c5ff'
  on-primary-fixed: '#001849'
  on-primary-fixed-variant: '#003fa4'
  secondary-fixed: '#69ff87'
  secondary-fixed-dim: '#3ce36a'
  on-secondary-fixed: '#002108'
  on-secondary-fixed-variant: '#00531e'
  tertiary-fixed: '#d3e4fe'
  tertiary-fixed-dim: '#b7c8e1'
  on-tertiary-fixed: '#0b1c30'
  on-tertiary-fixed-variant: '#38485d'
  background: '#f7f9fb'
  on-background: '#191c1e'
  surface-variant: '#e0e3e5'
typography:
  headline-xl:
    fontFamily: Inter
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 56px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
    letterSpacing: -0.01em
  headline-lg-mobile:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  headline-md:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-sm:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  label-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.01em
  label-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  unit: 4px
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 40px
  container-max: 1280px
  gutter: 24px
  margin-mobile: 16px
---

## Brand & Style
The design system embodies a "High-Tech Civic" personality—bridging the gap between advanced urban infrastructure and accessible public utility. It is defined by a **Corporate Modern** aesthetic that emphasizes clarity, efficiency, and intelligence. The target audience includes city officials, infrastructure engineers, and citizens, requiring a UI that feels authoritative yet effortless.

The visual direction is rooted in **Minimalism** with subtle **Glassmorphism** cues for overlays. By utilizing a "Bright White" foundation, the interface promotes a sense of transparency and cleanliness. The emotional response is one of reliability and forward-thinking precision, achieved through strict alignment, ample negative space, and a refined functional color application.

## Colors
This design system utilizes a high-clarity light mode palette to maximize legibility and professional atmosphere.

*   **Primary (Tech-Blue):** Used for primary actions, active states, and brand-critical iconography. It represents stability and connectivity.
*   **Secondary (Tech-Green):** Reserved for "Success" states, positive growth metrics, and active infrastructure status.
*   **Neutral (Slate/Cloud):** A scale of grays starting from white (#FFFFFF) to deep slate (#0F172A). Backgrounds utilize a very light tint (#F8FAFC) to differentiate surfaces from the pure white cards.
*   **Functional Accents:** Warning (Amber) and Error (Red) should be used sparingly, maintaining a low-vibrancy to ensure the Tech-Blue remains the dominant focal point.

## Typography
The typography system relies exclusively on **Inter** to maintain a systematic, utilitarian aesthetic. 

Headlines use a tighter letter-spacing and heavier weights to establish a clear hierarchy, while body text uses a standard weight for maximum readability in data-heavy contexts. Labels (used for buttons and table headers) may employ all-caps or medium weights to distinguish them from prose. Consistency in line-height is critical to maintaining the vertical rhythm of the grid-based layout.

## Layout & Spacing
The system utilizes a **12-column fluid grid** for desktop, transitioning to a 4-column grid for mobile. 

*   **Vertical Rhythm:** Built on a 4px baseline, with standard component heights following 32px, 40px, and 48px patterns.
*   **Grid Specs:** Desktop layouts use 24px gutters with 40px side margins. Tablets reduce gutters to 16px.
*   **Whitespace:** Generous padding within cards (minimum 24px) is mandatory to prevent information density from becoming overwhelming.
*   **Alignment:** All elements must snap to the grid. Forms and data visualizations should ideally span 6 or 12 columns to maintain structural balance.

## Elevation & Depth
Hierarchy is established through **Ambient Shadows** rather than heavy borders. 

*   **Surface Level (L0):** Background (#F8FAFC).
*   **Card Level (L1):** Pure White (#FFFFFF) with a soft, diffused shadow: `0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -2px rgba(0, 0, 0, 0.03)`.
*   **Overlay Level (L2):** Modals and dropdowns use a slightly more pronounced shadow and a 1px border (#E2E8F0) to ensure separation from the L1 surfaces.
*   **Active States:** Subtle inner shadows or light blue glints are used to indicate pressed states, maintaining a tactile but professional feel.

## Shapes
The shape language is **Rounded**, conveying modern accessibility. 

Standard components (Buttons, Inputs, Cards) use a **0.5rem (8px)** radius. Larger containers or "Hero" sections may scale up to **1rem (16px)** for a softer, more inviting look. Interactive elements like Toggles and Chips use fully rounded (Pill) shapes to clearly distinguish them from structural components.

## Components
*   **Buttons:** Primary buttons are solid Tech-Blue with white text. Secondary buttons use a subtle gray background (#F1F5F9) with Tech-Blue text.
*   **Cards:** Pure white backgrounds, 8px corner radius, and soft shadows. Content inside should have 24px padding.
*   **Tabs:** Modern "Underline" style for main navigation, or "Segmented" pill-style for sub-views, using a light gray track and white active indicator.
*   **Data Tables:** Clean, borderless rows with 1px horizontal dividers (#F1F5F9). Headers should be in `label-sm` with a light gray background. Row hover states should use a subtle blue tint (#EFF6FF).
*   **Form Controls:**
    *   **Inputs:** 1px border (#CBD5E1), turning Tech-Blue on focus.
    *   **Toggles:** iOS-style, using Tech-Green for the "On" state.
    *   **Sliders:** Thin Tech-Blue tracks with circular white thumbs containing a soft shadow.
*   **Chips/Tags:** Small, pill-shaped badges with low-opacity backgrounds (e.g., 10% Tech-Blue) and high-contrast text.