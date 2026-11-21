# Deploy Naija MenuShift to Streamlit Community Cloud

## Repository settings
- Repository: `Ibrahim-KIA/naija-menushift` (private)
- Branch: `main`
- Entrypoint: `app.py`
- Python: **3.11** (matches `.python-version`)
- Requirements: `requirements.txt` installs this package and its runtime dependencies using `-e .`
- Config: `.streamlit/config.toml`
- Secrets required: none for the synthetic prototype

## Owner deployment
1. Open https://share.streamlit.io and sign in with the GitHub account **Ibrahim-KIA**.
2. If this private repo does not appear, grant Streamlit Community Cloud access to *private* GitHub repositories in Workspace Settings → Linked accounts → Source control.
3. Click **Create app → Yup, I have an app**.
4. Use repository `Ibrahim-KIA/naija-menushift`, branch `main`, and file `app.py`; select **Python 3.11** in advanced settings.
5. Deploy and wait for the Cloud build to complete. Copy the actual `*.streamlit.app` URL *only after it is displayed*.
6. In the app, verify:
   - Synthetic-data warning appears; do not imply real price or nutrition validation.
   - Four tofu preparations and a beef **reference only**.
   - Budget/protein sensitivity, allergen exclusions, and no-feasible-option scenario.
   - The research-data mode refuses to invent missing measurements.
7. Since the GitHub repo is private, the new Streamlit app may be private by default. Invite collaborators as viewers or change app visibility **only if authorised**. Do not publish source credentials, contacts, or private research notes.
8. Share the verified Streamlit URL with the group. Any later push to main should update the deployed app automatically.

## Deployment support
- `ModuleNotFoundError: No module named 'menushift'`: check that `requirements.txt` is in root, contains `-e .`, and build logs show local package installation.
- Other import failures: inspect build logs and review `pyproject.toml` runtime dependencies; do not silently remove data checks.
- App displays missing research data: choose **Synthetic demonstration** mode. Source-backed mode stays gated until validated CSV files are populated.
- If the version causes issues, verify Python 3.11 selection and requirements against current Streamlit Cloud docs.
- GitHub Actions quality checks passing are necessary engineering evidence but **not** proof the deployed web UI works.

Official documentation:
- https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy
- https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies
- https://docs.streamlit.io/deploy/streamlit-community-cloud/share-your-app

**Do not invent a live app URL.** The user must complete the authenticated Streamlit Community Cloud deployment or use ChatGPT Work's connected cloud browser to do so.
