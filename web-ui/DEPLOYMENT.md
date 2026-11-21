# Vercel side-by-side demonstration

The existing Streamlit site remains unchanged: https://naija-menushift.streamlit.app/
The `web-ui/` folder provides a separate Next.js suya research prototype.
No AWS proxy, Bedrock, external model calls, or production API keys.

## Build
Run `npm ci`, `npm run typecheck`, `npm run build` in `web-ui/`.
The integrated GitHub Actions workflow runs those checks on this folder.

## Deploy
Import private GitHub `Ibrahim-KIA/naija-menushift` to Vercel.
Root directory `web-ui`, framework Next.js, Node 22.x; no environment variables.
Use only an eligible personal, non-commercial Hobby demonstration. Commercial
usage requires a compliant hosting arrangement. Do not treat the demo as verified
food-service software or as equal in coverage to the Python app.

## Smoke checks
- Public page renders without sign-in.
- POST /api/explore returns JSON for an ordinary brief.
- Invalid JSON, unsupported allergens and overlarge body receive 4xx.
- Soy and groundnut exclusions abstain, invalid seasoning origin abstains.
- Mobile viewport and keyboard controls work; compare with Streamlit.
