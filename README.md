# mods-registry

Model registry for [mods](https://github.com/modshq/mods) — the CLI model manager for AI image generation.

This repository contains YAML manifest files that describe models, LoRAs, VAEs, text encoders, and other assets. The `mods` CLI fetches a compiled index from this registry to know what's available and how to download it.

## Current Models

| Type | Count | Examples |
|------|-------|---------|
| Checkpoints | 4 | FLUX.1 Dev, FLUX.1 Schnell, SDXL Base, SD 1.5 |
| VAEs | 3 | Flux VAE, SDXL VAE fp16-fix, SD VAE ft-MSE |
| Text Encoders | 3 | T5-XXL fp16, T5-XXL fp8, CLIP-L |
| ControlNets | 1 | FLUX Depth |
| Upscalers | 2 | 4x UltraSharp, RealESRGAN x4plus |

## For Users

You don't interact with this repo directly. Just use the `mods` CLI:

```bash
mods update       # Fetches latest index from this registry
mods search flux  # Search available models
mods install flux-dev  # Install a model
```

## For Contributors

Want to add a model? See [CONTRIBUTING.md](CONTRIBUTING.md).

```bash
# Quick start
git clone https://github.com/modshq/mods-registry
cd mods-registry
pip install pyyaml

# Add your manifest
cp manifests/checkpoints/flux-dev.yaml manifests/checkpoints/my-model.yaml
# Edit the file...

# Validate
python scripts/validate.py manifests/checkpoints/my-model.yaml
python scripts/build_index.py
```

## License

MIT
