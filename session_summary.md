# USATT Automation & Dashboard: Session Summary

This document outlines the major upgrades and enhancements made to the USATT Ratings Automation pipeline and Web Dashboard during this session.

## 1. Advanced Tournament Selection & Validation

We completely overhauled how the `automator.py` script identifies and selects tournaments to calculate:
- **Boundary Detection**: The script now parses the Omnipong table to find the boundary between completed and upcoming tournaments.
- **Backward Accumulation**: Instead of just grabbing the top three, it traverses backward (chronologically) from the boundary, checking each tournament one by one.
- **Deduplication**: It safely skips any tournaments that have already been processed and exist in the workspace.
- **Intelligent Cell Validation**: Before downloading hundreds of matches, it parses the unique "Event Results" page for the tournament. 
  - *Refinement*: Initially, it checked every single cell, but this caused it to skip valid tournaments that simply lacked a 3rd/4th place playoff. We refined this logic to only check the **First Place** cell. If an event has a first-place finisher, the tournament is validated and approved for calculation!
- **Result**: The script autonomously accumulated exactly 3 brand new, 100% valid tournaments (like the *Silicon Valley Championships* and *Fremont TTA May Open*), securely generated their directories, downloaded their match data, and calculated all Elo permutations.

## 2. Multi-View Dashboard Upgrade

We transformed the static web interface into a dynamic, multi-view application:
- **Serverless Indexing**: The Python automator now dumps the names of all processed tournament folders into a `tournaments.json` file.
- **Home View (Tournament Grid)**: 
  - `index.html` and `script.js` were restructured to boot up and dynamically fetch the `tournaments.json` index.
  - The home screen now features a premium CSS Grid displaying stunning glassmorphism "Cards" for every available tournament.
- **Seamless Routing**: Clicking a tournament card smoothly transitions the interface to the **Tournament View** (the data table) without requiring a page reload.
  - The script dynamically loads the correct `calculated_ratings.csv` from the selected tournament's specific folder.
  - A new **"⬅ Back to Tournaments"** button allows users to return to the Home View instantly.

## 3. Dynamic Club Logo Integration

To further enhance the premium aesthetic of the dashboard:
- The tournament cards were updated to support dynamic, dimmed background images.
- If a user drops a `logo.jpg` into any tournament folder, the frontend will automatically detect it and render it as the card's background (`15% opacity`).
- Added subtle micro-animations where the logo gently scales up and brightens (`30% opacity`) when hovering over the card.
- If no logo is present, the card gracefully falls back to its default transparent glass style without any broken image errors.

## 4. Manual Rating Calculator (New Default View)

We introduced a comprehensive Manual Rating Calculator as the primary landing page:
- **Real-time USATT Logic**: The complete USATT rating algorithm (including point exchanges, unrated player logic, and the complex "Special Adjustment" multi-pass system) has been ported from Python to JavaScript.
- **Dual-Phase Calculation Display**: When a "Special Adjustment" is triggered, the dashboard now reveals an **Adjusted Rating** between the initial and final values.
- **Before/After Comparison**: Match results now display two sets of point calculations when adjusted:
    - **Initial**: Points gained/lost based on the starting rating.
    - **Adjusted**: Points gained/lost based on the new baseline (adjusted) rating, showing the direct impact of the adjustment on the final result.
- **Dynamic UI Adaptation**: The "Adjusted" column in the match list automatically hides if no adjustment is present, keeping the interface clean and focused.
- **Typographic Consistency**: Ensured consistent font rendering across all interactive elements, including inputs, buttons, and the new match entry bar.
- **Read-Only Match Verification**: Once a match is added via the entry bar, it is converted to stylized text and cannot be edited. This ensures that the calculated "Adjusted" and "Initial" point columns represent a fixed set of verified results, while still allowing for easy removal if a mistake is made.
- **Premium Typographic Rows**: Replaced interactive inputs with clean, bold typography for match results, improving readability and further aligning with the dashboard's professional aesthetic.
- **Seamless Navigation**: Integrated a multi-view navigation system that allows users to toggle between the manual calculator and the tournament results dashboard.
- **Premium UI**: Styled with glassmorphism, smooth animations, and responsive layouts to match the existing high-end aesthetic of the dashboard.

- All 6 previously calculated tournaments (including *Silicon Valley Championships*, *ICC JOOLA SPRING OPEN*, etc.) correctly populate the Home View grid!
- Clicking any of them instantly transitions the UI and injects their massive, 600+ match datatables directly into the view!
