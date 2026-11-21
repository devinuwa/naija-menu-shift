# Mobile, keyboard and browser release checks

**Status: not yet run in a rendered browser**. These are manual acceptance tests, not a certification claim. AppTest covers Python-side interaction; it cannot inspect CSS reflow, keyboard focus, zoom or screen-reader announcements.

## Public access
- [ ] Open https://naija-menushift.streamlit.app/ in an anonymous/incognito session, without Streamlit/GitHub login.
- [ ] Initial recommendation flow loads; no Streamlit access wall or unhandled exception.
- [ ] Fictional-data warning is displayed on first load. Data-source mode cannot accidentally present synthetic numbers as verified.

## Narrow screen (390 × 844, mobile portrait)
- [ ] Dish selector, budget, protein target, preference and result appear in logical reading order.
- [ ] Main action/result is visible without opening the sidebar.
- [ ] Inputs are not clipped or overlapping at 390px and 320px.
- [ ] Detailed data tables remain in secondary tabs/expanders and are usable by horizontal scroll.
- [ ] Displayed charts, alert messages, links and buttons are usable with touch targets.

## Zoom and contrast
- [ ] At 200% browser zoom, labels and validation messages remain visible.
- [ ] At 400% zoom / 320px effective viewport, no critical content is hidden behind the sidebar.
- [ ] Test text and alert contrast in light/dark OS settings; custom CSS must not hide focus indicators.
- [ ] Check styling without browser CSS injection tools, and inspect colour contrast using WCAG AA targets for normal text (4.5:1) and UI components (3:1), where applicable.

## Keyboard and assistive technology
- [ ] Tab through inputs, expanders, comparison tabs, tables and links; focus order follows the four-step flow.
- [ ] All controls have visible focus and accessible labels.
- [ ] Space/Enter selects recommendations, tabs and expanders without requiring a mouse.
- [ ] At least one screen-reader pass identifies the heading hierarchy, controls, result, error, status and synthetic-data warning.
- [ ] Switch to Research data: meaningful message explains missing validated inputs and never silently falls back.
- [ ] Tight budget: 'No plant-based option meets all ...' and clear reasons are visible, not only colour-dependent.
- [ ] Exclude soy: all tofu options correctly excluded. Exclude another allergen with unknown labels: abstain instead of asserting safety.

## Review record
Date:
Tester:
Browsers/platforms:
Screenshots/video evidence links:
Failed checks with reproduction steps:
Severity / owner:
PR linked to fixes:

This record should be filled after a real interactive browser session, **before merging and promoting the demo**.
