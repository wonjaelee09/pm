# Deployment options

## Vercel

1. Create a new GitHub repo.
2. Push this `app/` folder as the repo root.
3. Import the repo in Vercel.
4. Framework preset: Other / Static.
5. Build command: `npm run validate`.
6. Output directory: `.`.

## GitHub Pages

1. Push this `app/` folder as the repo root of a GitHub repo.
2. In GitHub repo settings, enable Pages via GitHub Actions.
3. Push to `main`.
4. The included workflow `.github/workflows/pages.yml` validates and deploys the static site.

## Local verification

```bash
npm run validate
python3 -m http.server 8095
```

Then open `http://127.0.0.1:8095` inside the same environment.
