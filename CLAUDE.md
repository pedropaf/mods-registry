# CLAUDE.md — Mods Registry

## What is this?

This is the **model registry** for [mods](https://github.com/modshq/mods) — the CLI model manager for AI image generation. It contains YAML manifest files describing models, LoRAs, VAEs, text encoders, recipes, and other assets, along with tooling to compile them into an `index.json` that the `mods` CLI fetches.

## Repository Structure

```
mods-registry/
  manifests/
    checkpoints/        # Checkpoint model manifests
    diffusion_models/   # Diffusion model manifests (FLUX Kontext, Z-Image, etc.)
    loras/              # LoRA adapter manifests (community + utility)
    vae/                # VAE manifests
    text_encoders/      # Text encoder manifests (CLIP, T5, etc.)
    controlnet/         # ControlNet manifests
    upscalers/          # Upscaler model manifests
    embeddings/         # Textual inversion embedding manifests
    ipadapters/         # IP-Adapter manifests
    segmentation/       # Segmentation model manifests
    recipes/            # Training preset manifests (the moat)
  schemas/
    manifest.schema.json  # JSON Schema for manifest validation
  scripts/
    build_index.py      # Compiles all manifests → index.json
    validate.py         # Validates manifests against schema
    verify_hashes.py    # Downloads files to verify SHA256 hashes
    fetch_hashes_from_hf.py  # Fetch hashes from HuggingFace via HEAD (no download)
    check_links.py      # Check all download URLs for link rot
  .github/
    workflows/
      ci.yml            # Validate manifests on PR
      publish.yml       # Build + publish index.json on merge to main
      link-check.yml    # Daily URL health check
  index.json            # Auto-generated compiled index (don't edit)
  CONTRIBUTING.md       # How to add models, LoRAs, and recipes
  README.md
```

## How It Works

1. Contributors add YAML manifest files in `manifests/<type>/`
2. CI validates the manifest against the schema
3. On merge to `main`, CI runs `build_index.py` which:
   - Reads all YAML manifests
   - Validates them
   - Compiles into a single `index.json` (v2 with metadata)
   - Publishes as a GitHub Release asset
4. The `mods` CLI fetches this `index.json` via `mods update`

## Index Format (v2)

The compiled `index.json` includes metadata:

```json
{
  "version": 2,
  "generated_at": "2026-02-27T12:00:00Z",
  "total_count": 65,
  "type_counts": { "checkpoint": 8, "diffusion_model": 17, "recipe": 4, ... },
  "cloud_available_count": 4,
  "schema_url": "https://registry.mods.sh/schemas/manifest.schema.json",
  "items": [...]
}
```

## Asset Types

| Type | Description |
|------|-------------|
| `checkpoint` | Full model checkpoint (single file, usually large) |
| `diffusion_model` | Standalone diffusion model (UNet/DiT, loaded separately) |
| `lora` | LoRA adapter (community-trained or utility) |
| `vae` | Variational autoencoder |
| `text_encoder` | Text encoder (CLIP, T5, etc.) |
| `controlnet` | ControlNet model |
| `upscaler` | Image upscaler |
| `embedding` | Textual inversion embedding |
| `ipadapter` | IP-Adapter model |
| `segmentation` | Image segmentation model |
| `recipe` | Training preset — no file, just configuration |

## Manifest Schema

Every manifest is a YAML file. Required fields:
- `id` — Unique identifier (lowercase, hyphens). Must match filename.
- `name` — Human-readable display name
- `type` — One of the asset types above
- Either `variants` (for multi-variant items) or `file` (for single-file items)
- **Exception**: `recipe` type requires `recipe` config instead of file/variants

### Common Optional Fields

`author`, `publisher`, `license`, `homepage`, `description`, `architecture`,
`requires`, `auth`, `defaults`, `tags`, `rating`, `downloads`, `preview_images`,
`added`, `updated`

### LoRA-Specific Fields

`base_models`, `trigger_words`, `recommended_weight`, `weight_range`,
`category`, `training_details`, `sample_images`

### Cloud Fields

- `cloud_available` — Boolean, model is on mods cloud
- `cloud_training` — GPU tier, estimated time, supported ranks
- `cloud_inference` — GPU tier, supports_lora, cold start time

### Recipe Fields

`recipe` object with: `base_model`, `training` (steps, lr, rank, etc.),
`generation` (steps, cfg, sampler), `tips`, `recommended_lora_weight`

See `schemas/manifest.schema.json` for the complete JSON Schema.

## Categories (for LoRAs and Recipes)

`general`, `style`, `character`, `concept`, `product`, `technique`,
`acceleration`, `editing`, `upscaling`, `segmentation`, `controlnet`

## SHA256 Hashes

**Every downloadable file must have a verified SHA256 hash.** Hashes marked with `VERIFY_` prefix are placeholders that need to be computed.

```bash
# Verify by downloading the file:
python scripts/verify_hashes.py manifests/checkpoints/flux-vae.yaml

# Fetch from HuggingFace without downloading (HEAD request):
python scripts/fetch_hashes_from_hf.py manifests/checkpoints/flux-dev.yaml

# Compute for a local file:
sha256sum path/to/model.safetensors
```

## Adding Content

### Model
1. Create YAML in `manifests/<type>/`, filename = `<id>.yaml`
2. Fill required fields + file/variants with SHA256 hashes
3. `python scripts/validate.py manifests/<type>/your-model.yaml`
4. `python scripts/build_index.py`
5. Submit PR

### Community LoRA
Same as model, but add `category`, `training_details`, `sample_images`,
`trigger_words`, `recommended_weight`. See CONTRIBUTING.md.

### Recipe
1. Create YAML in `manifests/recipes/`
2. Fill `recipe` config (base_model, training params, generation defaults, tips)
3. No file/variants needed — recipes are pure configuration
4. Validate and submit PR

## Scripts

All scripts require Python 3.10+ and PyYAML (`pip install pyyaml`).

- `python scripts/build_index.py` — Build index.json from all manifests
- `python scripts/build_index.py --output dist/index.json` — Custom output path
- `python scripts/validate.py [file...]` — Validate specific or all manifests
- `python scripts/verify_hashes.py <file>` — Download and verify SHA256
- `python scripts/fetch_hashes_from_hf.py` — Fix all VERIFY_ placeholders via HF API
- `python scripts/check_links.py` — Check all download URLs for broken links

## Code Conventions

- Manifest filenames: lowercase, hyphens, `.yaml` extension
- IDs: lowercase, hyphens only (e.g., `flux-dev`, `t5-xxl-fp16`)
- Sizes: in bytes (integer)
- VRAM: in MB (integer)
- URLs: direct download links (no redirects requiring JS)
- Hashes: lowercase hex SHA256
- Dates: ISO 8601 format (YYYY-MM-DD)
