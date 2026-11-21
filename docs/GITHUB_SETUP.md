# Create the private GitHub repository and invite contributors

**Prepared target:** `https://github.com/Ibrahim-KIA/naija-menushift` (this link will work **only after** creation and an initial push).

## 1. Create repository

1. While signed into `Ibrahim-KIA`, open <https://github.com/new>.
2. Owner: `Ibrahim-KIA`. Name: `naija-menushift`.
3. Choose **Private**. Do **not** auto-generate a README, license or `.gitignore` (all source files are in this bundle).
4. Create repository.

## 2. Publish from local working folder

Extract the project ZIP and open PowerShell in the `naija-menushift` folder:

```powershell
git init -b main
git add .
git commit -m "Bootstrap multi-dish menu innovation prototype"
git remote add origin https://github.com/Ibrahim-KIA/naija-menushift.git
git push -u origin main
```

If the extracted bundle contains `.git`, skip `git init`, `git add`, and `git commit` and push directly. If the branch is not `main`, run `git branch -M main`. Use your normal GitHub authentication; don't paste tokens into files or the chat.

Alternative: GitHub's web **Add file → Upload files** can upload text files into a blank repository, but preserving nested directories is easiest with Git.

## 3. Invite collaborators

Repo → **Settings → Collaborators and teams → Add people**:

- Search username **`devinuwa`** and invite Muhammad Inuwa; wait for acceptance.
- Invite Amina using her GitHub account (use the email in the *separate private invitation checklist* or obtain her username; email may need to be associated with her GitHub account). Wait for acceptance.

Both need at least **Write** access for code contributions; avoid granting Admin unless necessary. CODEOWNERS mentions Muhammad but does not create permissions. Do not make the repo public before reviewing source and personal-data policy.

## 4. Complete project hygiene

- Settings → General: keep issues enabled.
- Settings → Branches / Rules: protect `main`, require PRs and passing tests if supported for your plan.
- Actions: verify `Tests and static checks` workflow.
- Create the tasks from `docs/TASKS.md` as separate issues and assign them **after invitation acceptance**.
- Update `.github/CODEOWNERS` to add Amina's confirmed GitHub username after she accepts.

## 5. Verify

Check that `README.md`, `app.py`, `data/`, `src/`, `.github/workflows/ci.yml` and tests appear in GitHub. Check that invitations show as pending/accepted, and that the green checks reflect **actual CI** rather than local tests. No collaborator has access until the repository exists and their invitation has been sent and accepted.
