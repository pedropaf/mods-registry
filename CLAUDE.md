# CLAUDE.md — Mods Registry

## What is this?

This is the **model registry** for [mods](https://github.com/modshq/mods) — the CLI model manager for AI image generation. It contains YAML manifest files describing models, LoRAs, VAEs, text encoders, and other assets, along with tooling to compile them into an `index.json` that the `mods` CLI fetches.

## Repository Structure

```
mods-registry/
  manifests/
    checkpoints/        # Checkpoint model manifests
    loras/              # LoRA adapter manifests
    vae/                # VAE manifests
    text_encoders/      # Text encoder manifests (CLIP, T5, etc.)
    controlnet/         # ControlNet manifests
    upscalers/          # Upscaler model manifests
    embeddings/         # Textual inversion embedding manifests
    ipadapters/         # IP-Adapter manifests
  schemas/
    manifest.schema.json  # JSON Schema for manifest validation
  scripts/
    build_index.py      # Compiles all manifests → index.json
    validate.py         # Validates manifests against schema
    verify_hashes.py    # Downloads files to verify SHA256 hashes
  .github/
    workflows/
      ci.yml            # Validate manifests on PR
      publish.yml       # Build + publish index.json on merge to main
  index.json            # Auto-generated compiled index (don't edit)
  CONTRIBUTING.md       # How to add models
  README.md
```

## How It Works

1. Contributors add YAML manifest files in `manifests/<type>/`
2. CI validates the manifest against the schema
3. On merge to `main`, CI runs `build_index.py` which:
   - Reads all YAML manifests
   - Validates them
   - Compiles into a single `index.json`
   - Publishes as a GitHub Release asset
4. The `mods` CLI fetches this `index.json` via `mods update`

## Manifest Schema

Every manifest is a YAML file. Required fields:
- `id` — Unique identifier (lowercase, hyphens). Must match filename.
- `name` — Human-readable display name
- `type` — One of: checkpoint, lora, vae, text_encoder, controlnet, upscaler, embedding, ipadapter
- Either `variants` (for multi-variant items like checkpoints) or `file` (for single-file items like LoRAs)
- Every file entry needs: `url`, `sha256`, `size`, `format`

Optional fields: `author`, `license`, `homepage`, `description`, `architecture`, `requires`, `auth`, `defaults`, `base_models`, `trigger_words`, `tags`, `rating`, `downloads`, `preview_images`, `added`, `updated`

See existing manifests for examples.

## SHA256 Hashes

**Every file must have a verified SHA256 hash.** Hashes marked with `VERIFY_` prefix are placeholders that need to be computed by downloading the actual file.

To verify a hash:
```bash
python scripts/verify_hashes.py manifests/checkpoints/flux-vae.yaml
```

Or compute a hash for a local file:
```bash
sha256sum path/to/model.safetensors
```

## Adding a Model

1. Create a YAML file in the appropriate `manifests/<type>/` directory
2. Filename must match the `id` field (e.g., `flux-dev.yaml` has `id: flux-dev`)
3. Fill in all required fields
4. Run `python scripts/validate.py manifests/<type>/your-model.yaml`
5. Run `python scripts/build_index.py` to verify it compiles
6. Submit a PR

## Scripts

All scripts require Python 3.10+ and PyYAML (`pip install pyyaml`).

- `python scripts/build_index.py` — Build index.json from all manifests
- `python scripts/validate.py [file...]` — Validate specific manifests
- `python scripts/validate.py` — Validate all manifests
- `python scripts/verify_hashes.py <file>` — Download and verify SHA256 for a manifest

## Code Conventions

- Manifest filenames: lowercase, hyphens, `.yaml` extension
- IDs: lowercase, hyphens only (e.g., `flux-dev`, `t5-xxl-fp16`)
- Sizes: in bytes (integer)
- VRAM: in MB (integer)
- URLs: direct download links (no redirects requiring JS)
- Hashes: lowercase hex SHA256
- Dates: ISO 8601 format (YYYY-MM-DD)
