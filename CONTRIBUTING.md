# Contributing to mods-registry

Thank you for contributing model manifests! This registry powers the `mods` CLI model manager.

## Adding a Model

### 1. Choose the Right Directory

| Model Type | Directory | Example |
|------------|-----------|---------|
| Checkpoint | `manifests/checkpoints/` | FLUX.1 Dev, SDXL |
| Diffusion Model | `manifests/diffusion_models/` | FLUX Kontext, Z-Image Turbo |
| LoRA | `manifests/loras/` | Realistic skin, style LoRAs |
| VAE | `manifests/vae/` | SDXL VAE, Flux VAE |
| Text Encoder | `manifests/text_encoders/` | CLIP-L, T5-XXL |
| ControlNet | `manifests/controlnet/` | Depth, Canny |
| Upscaler | `manifests/upscalers/` | 4x UltraSharp |
| Embedding | `manifests/embeddings/` | Textual inversions |
| IP-Adapter | `manifests/ipadapters/` | FaceID, Plus |
| Segmentation | `manifests/segmentation/` | BiRefNet DIS |
| Recipe | `manifests/recipes/` | Training presets |

### 2. Create a YAML Manifest

Create a file named `<id>.yaml` in the appropriate directory. The `id` must be lowercase with hyphens only.

**Minimum required fields:**

```yaml
id: my-model-name
name: "My Model Display Name"
type: checkpoint  # or lora, vae, etc.

# For single-file models (LoRAs, VAEs, etc.):
file:
  url: https://direct-download-url.com/model.safetensors
  sha256: "abc123..."  # Full SHA256 hash
  size: 186000000      # Size in bytes (integer)
  format: safetensors

# For multi-variant models (checkpoints with fp16/fp8/etc.):
variants:
  - id: fp16
    file: model-fp16.safetensors
    url: https://...
    sha256: "..."
    size: 23800000000
    format: safetensors
    precision: fp16
    vram_required: 24576   # MB
```

### 3. Get the SHA256 Hash

```bash
# If you have the file locally:
sha256sum path/to/model.safetensors

# Or use the verification script (downloads the file):
python scripts/verify_hashes.py manifests/checkpoints/my-model.yaml

# Or fetch from HuggingFace without downloading (uses HEAD request):
python scripts/fetch_hashes_from_hf.py manifests/checkpoints/my-model.yaml
```

### 4. Validate

```bash
pip install pyyaml
python scripts/validate.py manifests/checkpoints/my-model.yaml
python scripts/build_index.py  # Make sure it compiles
```

### 5. Submit a PR

- One manifest per PR (unless adding a model with its dependencies)
- Include a brief description of the model
- Make sure `validate.py` passes
- Placeholder hashes (`VERIFY_...`) are acceptable in PRs — maintainers will verify

---

## Adding a Community LoRA

Trained a LoRA with `mods train`? Publish it to share with others.

```yaml
id: my-portrait-lora
name: "Anime Portrait Style v2"
type: lora
architecture: flux
author: your-username
license: cc-by-4.0
description: |
  Anime portrait style LoRA trained on 25 images.
  Creates consistent anime-style portraits with detailed eyes and hair.

category: style  # one of: style, character, concept, product, technique, acceleration

base_models: [flux-schnell, flux-dev]

file:
  url: https://huggingface.co/your-username/anime-portrait-v2/resolve/main/model.safetensors
  sha256: "..."
  size: 186000000
  format: safetensors

trigger_words: ["anime portrait style"]
recommended_weight: 0.75
weight_range: [0.5, 1.0]

# How it was trained (optional but encouraged)
training_details:
  steps: 2000
  rank: 32
  learning_rate: 5e-5
  optimizer: adamw8bit
  dataset_size: 25
  training_time_minutes: 15
  cloud_trained: true
  recipe_id: flux-style-lora  # links to the recipe used

# Show what it can do (highly encouraged)
sample_images:
  - url: https://example.com/sample1.png
    prompt: "anime portrait of a woman with long silver hair, detailed eyes"
    steps: 8
    cfg: 3.5

tags: [anime, portrait, style, flux]
added: "2026-02-27"
```

### LoRA Categories

| Category | Use for |
|----------|---------|
| `style` | Artistic styles, illustration aesthetics, rendering techniques |
| `character` | Specific people, characters, faces |
| `concept` | Abstract concepts, poses, compositions |
| `product` | Specific products, objects, brands |
| `technique` | Photography techniques, lighting styles |
| `acceleration` | Speed/distillation LoRAs (LCM, Turbo) |

---

## Adding a Recipe

Recipes are training presets — the best parameters for a specific use case.

```yaml
id: flux-my-usecase
name: "My Use Case LoRA (Flux)"
type: recipe
architecture: flux
author: your-username
license: mit
description: |
  Training recipe for [use case] LoRAs on Flux models.
  Explain what this produces and when to use it.

category: style  # or character, product, etc.

recipe:
  base_model: flux-schnell
  description: |
    Best for: [what it does well]
    Dataset: [how many images, what kind]
    Result: [what you get]
  training:
    steps: 1500
    learning_rate: 1e-4
    rank: 16
    optimizer: adamw8bit
    batch_size: 1
    resolution: "1024x1024"
    dataset_min_images: 10
    dataset_max_images: 30
    caption_strategy: florence-2
    trigger_word_template: "sks style"
  generation:
    steps: 8
    cfg: 3.5
    sampler: euler
    scheduler: normal
  recommended_lora_weight: 0.8
  tips:
    - "Practical tip #1"
    - "Practical tip #2"

tags: [recipe, your-tags]
added: "2026-02-27"
```

Recipes don't have `file` or `variants` — they're pure configuration.

---

## Guidelines

- **Direct download URLs only.** No JavaScript-required downloads. HuggingFace `/resolve/main/` URLs work great.
- **Accurate file sizes.** Use exact byte counts, not approximations.
- **Proper licensing.** Include the correct license identifier.
- **Dependencies.** If a model requires a VAE or text encoder, add it to `requires`.
- **Don't modify index.json.** It's auto-generated by CI.

## Schema

All manifests are validated against [manifest.schema.json](schemas/manifest.schema.json).

## Questions?

Open an issue if you need help adding a model, LoRA, or recipe.
