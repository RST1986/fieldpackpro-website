# FieldPack Pro Website

Public static site for FieldPack Pro Jamaica: landing page, privacy policy and support content for `fieldpackpro.com`.

## Hosting boundary

The site is prepared for Cloudflare Pages. Public assets must be self-hosted in this repository or loaded only from explicitly permitted origins. Netlify references are prohibited.

`_headers` defines the static security-header baseline for Cloudflare Pages, including CSP, HSTS, nosniff, clickjacking protection, referrer policy and permissions policy.

## Validation

Run the repository gate before review:

```bash
python3 scripts/validate_site.py
```

The validator fails closed on broken local references, Netlify links, insecure `http://` references, missing image alt text, inline JavaScript/event handlers and missing security-header controls.

## Release governance

A green CI run verifies static-site contracts only. It does not authorise DNS changes, Cloudflare production promotion, legal/privacy claims, procurement claims, product capability activation or any other production state change.

`TEST_PASS != PRODUCTION_APPROVAL`
