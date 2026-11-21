# Security and responsible use

This is a student research prototype. Do not use it to make food-safety, allergy-safety, medical, or nutrition sufficiency guarantees. Reviewers must verify commercial use against applicable food standards.

- Never commit passwords, API keys, private participants' information, restaurant quotes supplied in confidence, or credentials.
- Store secrets in ignored `.streamlit/secrets.toml` or environment variables, never in Git.
- Screen user-supplied CSVs; the loader fails on missing provenance and prohibited animal ingredients in plant options but is not a comprehensive safety audit.
- Prepare synthetic presentations without implying laboratory or taste validation.
- For security concerns, report privately to the repository owner rather than opening an issue containing secrets.
