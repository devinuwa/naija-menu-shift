# Developer tools & optional agent skills

- **Core:** Python 3.11+, pytest, Ruff, Streamlit, pandas, scikit-learn, Git and GitHub Actions.
- **Editor:** Codex or Claude Code can read root `AGENTS.md`; three repo-local skills in `.agents/skills/` guide research, recommender engineering and Streamlit UX.
- **Streamlit official skills:** after environment install, run `streamlit skills --yes` from the repository. This creates local symlinks to the bundled Streamlit skills, so agents follow current framework guidance. This step is optional and not yet run in CI.
- **Security:** Avoid storing API keys; the first pilot needs none. Use a private repository, least-privilege collaborators, CI on PRs, and Dependabot review.
- **Deployment:** currently a local research app. Deploy only after owner approval, verified demo disclaimer, and access controls are decided. No public site or hosted database was created by this repository.

See official docs: <https://docs.streamlit.io/develop/api-reference/cli/skills> and <https://docs.github.com/en/actions/security-for-github-actions/security-guides/security-hardening-for-github-actions>.
