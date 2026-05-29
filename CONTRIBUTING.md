# Contributing

## 🌿 Branch Strategy

- `main` — produção, protegida. Só recebe merge de `dev` via PR aprovado.
- `dev` — integração. Features convergem aqui antes de subir pra `main`.
- `feature/*` — branches de trabalho individuais. Efêmeras — nascem, recebem commits, abrem PR contra `dev` e morrem após merge.
- `fix/*` — correções de bugs.
- `docs/*` — documentação.
- `ci/*` — CI/CD.

⚠️ **Sempre `dev`, nunca `develop`.**

## 📝 Commits

Seguimos [Conventional Commits](https://www.conventionalcommits.org/):

```
type(scope): descrição curta
```

**Tipos:** `feat`, `fix`, `refactor`, `docs`, `test`, `ci`, `chore`, `perf`

**Exemplos:**
```
feat(profile): add extended profile endpoint
fix(auth): handle expired token gracefully
docs(readme): add setup instructions
```

## 🔀 Pull Requests

1. Crie sua branch a partir de `dev`
2. Faça commits com mensagens padronizadas
3. Abra PR contra `dev` com:
   - Título no formato conventional commit
   - Descrição clara do que foi feito
   - Como testar
   - Screenshots se houver mudança visual
   - Issues relacionadas (`Closes #X`)
4. Aguarde review e CI verde
5. Merge squash (`feature/*` → `dev`) ou merge commit (`dev` → `main`)

## 🏷️ Versionamento

[SemVer](https://semver.org/): `MAJOR.MINOR.PATCH`
- MAJOR: quebra compatibilidade (muda API pública)
- MINOR: nova feature compatível (novo endpoint)
- PATCH: correção de bug

## 🧰 Setup Local

```bash
git clone git@github.com:duribeiro/linkedin-mcp.git
cd linkedin-mcp
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Preencha CLIENT_ID e CLIENT_SECRET do LinkedIn
```

Consulte o `README.md` para instruções detalhadas.
