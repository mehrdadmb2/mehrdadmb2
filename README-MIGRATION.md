# Migration checklist

## Remove conflicting files

Delete old workflows that produce the same profile assets, for example:

```text
.github/workflows/metrics.yml          # replace with the supplied version
.github/workflows/profile-3d-contrib.yml
.github/workflows/snake.yml
```

If you already have a different workflow for blog posts, replace it with the supplied `blog-posts.yml` instead of running both.

## Keep your existing backup files

Files such as historical README backups can stay. They do not affect the profile unless they are named `README.md` or are referenced by an active workflow.

## Canonical structure

```text
.
├── README.md
├── SETUP.md
├── README-MIGRATION.md
├── assets/
│   ├── banner.svg
│   ├── status.svg
│   ├── stack.svg
│   ├── footer.svg
│   ├── snake.svg
│   ├── snake-dark.svg
│   └── qr/
│       ├── ton.svg
│       ├── trc20-usdt.svg
│       ├── ethereum.svg
│       ├── bitcoin.svg
│       ├── solana.svg
│       ├── bnb.svg
│       ├── polygon.svg
│       └── tron.svg
├── scripts/
│   ├── generate_qr.py
│   └── generate_visual_assets.py
└── .github/
    ├── ISSUE_TEMPLATE/
    │   ├── contact.yml
    │   └── config.yml
    └── workflows/
        ├── metrics.yml
        ├── blog-posts.yml
        └── snake.yml
```
