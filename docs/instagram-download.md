# Instagram Download Workflow

This workflow uses `gallery-dl` with logged-in browser cookies to download recent Instagram profile images into a local folder.

Use only accounts and content you are authorized to access.

## Command

```bash
./scripts/instagram/download_ig.command example_profile 20 chrome
```

Arguments:

```text
./scripts/instagram/download_ig.command <profile_name> <recent_post_count> <browser>
```

Examples:

```bash
./scripts/instagram/download_ig.command lowclassic_seoul 20 chrome
./scripts/instagram/download_ig.command example_profile 12 safari
```

## Output

The helper writes files under:

```text
scripts/instagram/downloads/<profile_name>/
```

It also writes:

```text
scripts/instagram/archive/<profile_name>.txt
scripts/instagram/logs/<profile_name>_<timestamp>.log
```

## Use With Brand Matching

```bash
python3 scripts/build_brand_url_matches.py \
  --url "https://example-brand.com/" \
  --instagram-folder "scripts/instagram/downloads/example_profile" \
  --brand-slug example_brand
```

The brand matching script reads image sidecar JSON metadata, sorts Instagram images by `post_date`, and uses at most two images per post by default.

## Troubleshooting

- Confirm you are logged in to Instagram in the chosen browser.
- Use a profile id, not a full URL, for the download command.
- If images do not download, inspect `scripts/instagram/logs/`.
- If one carousel is too dominant, keep the default `--instagram-max-images-per-post 2` behavior in the brand matching step.
