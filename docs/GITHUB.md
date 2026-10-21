# Publish and onboard a colleague

Repository: https://github.com/JozsefKiss90/ai-second-brain

The current repository is public. This repository shares application code and
synthetic examples only. Anyone can clone it; collaborator access is needed only
for direct contributions, not ordinary use. Use a private repository if you
intend to restrict access to the software itself.

## Publishing a separate copy (optional)

1. Sign in to GitHub and create an **empty private repository** named
   ai-second-brain. Do not initialize it with a README, license or gitignore.
2. In the root of this prepared project, review `git status` and files to commit.
   Personal workspace, .venv and generated config must remain excluded.
3. If working from the ZIP, initialize and commit:

```powershell
git init -b main
git add .
git status
git commit -m "Add personal coding workflow Second Brain starter"
```

4. Connect and push, replacing YOUR_ACCOUNT with the actual owner:

```powershell
git remote add origin https://github.com/YOUR_ACCOUNT/ai-second-brain.git
git push -u origin main
```

If the project is already a Git checkout with a commit, skip reinitialization and
commit; inspect `git remote -v` before adding a remote. Authenticate using your
normal Git Credential Manager/browser flow. Never put a token in a remote URL.

5. Repository Settings → Collaborators: invite the intended colleague by her
   verified GitHub username. Choose access suitable for whether she only uses
   the application or also contributes code. She must accept the invitation.

Do not guess which GitHub account belongs to her. For an assistant to issue an
invitation, supply her exact username and desired permission.

## Colleague's first session

1. Open the repository URL above. A public clone does not need an invitation.
2. Install/check the prerequisites in WINDOWS.md.
3. Clone `https://github.com/JozsefKiss90/ai-second-brain.git` into her own Projects folder.
4. Run setup.ps1; confirm tests pass.
5. Copy only synthetic examples first, run sync, and verify one cited answer.
6. Connect her own free model account and optional OpenAI account in OpenCode.
7. Edit her own profile using WORKFLOWS.md.
8. Import a handful of her own non-sensitive notes; test five real questions.

She does not need your local folder, database, API key, OpenCode authentication,
or Windows account. You do not need access to her personal memory.

## Collaboration options

- Shared software: both clone this repository and contribute through branches/PRs.
- Independent ownership: create a separate repository from the same starter code.
- Shared organizational knowledge: future explicit export/import of curated notes;
  not provided as automatic database sharing. Do not commit a live private index.

This package does not automatically create a GitHub repository, enable GitHub's
"Template repository" setting, invite anyone, or send a notification.

No open-source license is assigned by this starter. Keep the repository private
for colleague collaboration and choose an appropriate license before a public
release if you want others to reuse it under explicit terms.
