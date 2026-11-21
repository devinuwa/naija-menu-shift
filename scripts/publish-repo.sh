#!/usr/bin/env bash
set -euo pipefail
# Run after manually creating the EMPTY PRIVATE GitHub repository in your account.
if [[ ! -d .git ]]; then
  git init -b main
  git add .
  git commit -m "Bootstrap Naija MenuShift prototype"
fi
if git remote get-url origin >/dev/null 2>&1; then
  echo 'Remote origin already exists; inspect it and push manually.' >&2
  exit 1
fi
git remote add origin 'https://github.com/Ibrahim-KIA/naija-menushift.git'
git push -u origin main
