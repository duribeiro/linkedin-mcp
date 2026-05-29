# Contributing

## 🌿 Branch Strategy

- `main` — production, protected. Only receives merges from `dev` via approved PR.
- `dev` — integration. Features converge here before going up to `main`.
- `feature/*` — individual work branches. Ephemeral — born, committed, PR'd against `dev`, and deleted after merge.
- `fix/*` — bug fixes.
- `docs/*` — documentation.
- `ci/*` — CI/CD pipeline changes.

⚠️ **Always `dev`, never `develop`.**

## 📝 Commits

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
type(scope): short description
```

**Types:** `feat`, `fix`, `refactor`, `docs`, `test`, `ci`, `chore`, `perf`

**Examples:**
```
feat(profile): add extended profile endpoint
fix(auth): handle expired token gracefully
docs(readme): add setup instructions
```

## 🔀 Pull Requests

1. Create your branch from `dev`
2. Commit with standardized messages
3. Open PR against `dev` with:
   - Title in conventional commit format
   - Clear description of what was done
   - How to test
   - Screenshots if there are visual changes
   - Related issues (`Closes #X`)
4. Wait for review and green CI
5. Squash merge (`feature/*` → `dev`) or merge commit (`dev` → `main`)

## 🏷️ Versioning

[SemVer](https://semver.org/): `MAJOR.MINOR.PATCH`
- MAJOR: breaking changes (public API change)
- MINOR: backwards-compatible new feature (new endpoint)
- PATCH: bug fix

## 🧰 Local Setup

```bash
git clone git@github.com:duribeiro/linkedin-mcp.git
cd linkedin-mcp
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Fill in CLIENT_ID and CLIENT_SECRET from LinkedIn
```

See `README.md` for detailed instructions.
