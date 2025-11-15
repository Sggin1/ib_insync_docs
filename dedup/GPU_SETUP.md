# GPU Setup Guide - 16GB GPU Configuration

**Hardware:** 16GB GPU (NVIDIA recommended)
**Tools Available:** Ollama, LM Studio, Docker
**Goal:** Maximize local inference performance for deduplication

---

## Quick Start (Recommended Setup)

### 1. GPU Configuration

Your 16GB GPU enables:
- **Larger local models** (14B-33B parameters quantized)
- **Faster embeddings** (GPU-accelerated)
- **Better quality** without API costs
- **Higher throughput** (batch processing)

### 2. Recommended Stack

**Option A: Ollama + GPU (Easiest)**
```bash
# Install Ollama (if not already)
curl -fsSL https://ollama.ai/install.sh | sh

# Pull recommended model (fits 16GB)
ollama pull qwen2.5:14b

# Test it
ollama run qwen2.5:14b "Explain code deduplication"

# For embeddings, install with GPU support
pip install sentence-transformers torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

**Option B: LM Studio (GUI, Great for Testing)**
- Download from: https://lmstudio.ai/
- Load model: `TheBloke/Qwen2.5-14B-Instruct-GGUF` (Q4_K_M quantization)
- Enable GPU acceleration in settings
- Start local server on port 1234

**Option C: vLLM + Docker (Highest Performance)**
```bash
# Run vLLM in Docker with GPU
docker run --gpus all -p 8000:8000 \
  -v ~/.cache/huggingface:/root/.cache/huggingface \
  vllm/vllm-openai:latest \
  --model Qwen/Qwen2.5-14B-Instruct \
  --gpu-memory-utilization 0.9 \
  --max-model-len 8192
```

---

## Model Recommendations for 16GB GPU

### Local LLM (for merging)

**Best Overall: Qwen2.5 14B**
```bash
# Ollama
ollama pull qwen2.5:14b

# LM Studio
# Download: TheBloke/Qwen2.5-14B-Instruct-GGUF (Q4_K_M)

# Performance: ~15-25 tokens/sec on 16GB GPU
# Quality: Excellent code understanding
# Memory: ~10-12GB VRAM
```

**Best for Code: DeepSeek-Coder 33B (Quantized)**
```bash
# Ollama
ollama pull deepseek-coder:33b-instruct-q4_K_M

# Performance: ~8-12 tokens/sec
# Quality: Superior code analysis
# Memory: ~14-15GB VRAM
# Note: Slower but better for complex code merges
```

**Fast & Efficient: Qwen2.5 7B**
```bash
# Ollama
ollama pull qwen2.5:7b

# Performance: ~40-60 tokens/sec
# Quality: Good for simple merges
# Memory: ~5-6GB VRAM
# Best for: High throughput, simple cases
```

**Reasoning: Mixtral 8x7B**
```bash
# Ollama
ollama pull mixtral:8x7b-instruct-v0.1-q4_K_M

# Performance: ~10-15 tokens/sec
# Quality: Excellent reasoning
# Memory: ~13-14GB VRAM
# Best for: Complex decisions
```

### Embeddings (for clustering)

**Recommended: all-mpnet-base-v2**
```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-mpnet-base-v2')
model = model.to('cuda')  # Use GPU

# Dimensions: 768
# Quality: Excellent semantic similarity
# Speed: ~500-1000 sentences/sec on GPU
```

**State-of-the-Art: BGE-Large**
```python
model = SentenceTransformer('BAAI/bge-large-en-v1.5')
model = model.to('cuda')

# Dimensions: 1024
# Quality: Best available
# Speed: ~300-500 sentences/sec
# Note: Slightly slower but highest quality
```

**Fast Option: MiniLM**
```python
model = SentenceTransformer('all-MiniLM-L6-v2')
model = model.to('cuda')

# Dimensions: 384
# Quality: Good
# Speed: ~1500-2000 sentences/sec
# Best for: Quick iterations
```

---

## Configuration Examples

### Full GPU Setup (Recommended)

```yaml
# config.yaml
ai:
  mode: local_only  # No API costs!

  local:
    provider: ollama
    model: qwen2.5:14b
    temperature: 0.3
    timeout: 120
    ollama:
      host: http://localhost:11434
      num_gpu: 1

embeddings:
  model: all-mpnet-base-v2
  device: cuda
  batch_size: 64
  gpu_id: 0
  precision: float16
```

### Hybrid with OpenRouter (Fallback)

```yaml
ai:
  mode: hybrid

  local:
    provider: ollama
    model: qwen2.5:14b

  openrouter:
    api_key: ${OPENROUTER_API_KEY}
    model: anthropic/claude-3.5-sonnet
    max_budget: 2.00

  hybrid:
    use_local_for_most: true  # 90% local, 10% OpenRouter
```

### LM Studio Setup

```yaml
ai:
  local:
    provider: lmstudio
    model: qwen2.5:14b  # Name doesn't matter for LM Studio
    lmstudio:
      host: http://localhost:1234
      gpu_layers: -1  # Use all GPU
```

---

## Performance Benchmarks (16GB GPU)

### Embedding Generation
| Model | Dimensions | Speed (sentences/sec) | VRAM Usage |
|-------|------------|----------------------|------------|
| MiniLM-L6-v2 | 384 | ~1500-2000 | 1GB |
| mpnet-base-v2 | 768 | ~500-1000 | 2GB |
| BGE-large | 1024 | ~300-500 | 3GB |

**For our use case (~300 examples):**
- MiniLM: <1 second
- mpnet: 1-2 seconds
- BGE: 2-3 seconds

**Recommendation:** Use `all-mpnet-base-v2` for best quality/speed balance

### LLM Inference (Merging ~200 clusters)
| Model | Tokens/sec | Time per Merge | Total Time | VRAM |
|-------|-----------|----------------|------------|------|
| Qwen 7B | 40-60 | ~10-15 sec | ~30-50 min | 6GB |
| Qwen 14B | 15-25 | ~20-30 sec | ~60-100 min | 12GB |
| DeepSeek 33B | 8-12 | ~40-60 sec | ~120-200 min | 15GB |
| Mixtral 8x7B | 10-15 | ~30-45 sec | ~90-150 min | 14GB |

**Recommendation:**
- **Development:** Qwen 7B (fast iteration)
- **Production:** Qwen 14B (best balance)
- **Maximum Quality:** DeepSeek 33B (if time permits)

---

## Setup Instructions

### 1. Verify GPU

```bash
# Check NVIDIA GPU
nvidia-smi

# Check CUDA version
nvcc --version

# Expected: CUDA 11.8 or 12.x
```

### 2. Install PyTorch with GPU Support

```bash
# For CUDA 11.8
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118

# For CUDA 12.1
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121

# Test GPU
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}'); print(f'GPU: {torch.cuda.get_device_name(0)}')"
```

### 3. Setup Ollama with GPU

```bash
# Ollama automatically detects GPU, just pull models
ollama pull qwen2.5:14b

# Test GPU usage
ollama run qwen2.5:14b

# Monitor GPU usage in another terminal
watch -n 0.5 nvidia-smi
```

### 4. Install sentence-transformers with GPU

```bash
pip install sentence-transformers

# Test
python -c "from sentence_transformers import SentenceTransformer; m = SentenceTransformer('all-mpnet-base-v2'); print(m.device)"
```

### 5. Update Config

```bash
cd dedup
cp config.yaml.example config.yaml

# Edit config.yaml:
# - Set embeddings.device: cuda
# - Set ai.local.model: qwen2.5:14b
# - Increase batch sizes
```

---

## OpenRouter Integration

OpenRouter gives you access to many models through one API:

### Setup

```bash
# Get API key from: https://openrouter.ai/keys
export OPENROUTER_API_KEY="your-key-here"

# Or add to config.yaml
```

### Available Models (via OpenRouter)

**Recommended:**
- `anthropic/claude-3.5-sonnet` - $3/M tokens (same as direct)
- `qwen/qwen-2.5-72b-instruct` - $0.36/M tokens (cheap, good)
- `deepseek/deepseek-coder` - $0.14/M tokens (very cheap for code)
- `google/gemini-pro-1.5` - $1.25/M tokens
- `meta-llama/llama-3.1-70b-instruct` - $0.52/M tokens

**Cost Comparison (for 200 merges):**
- Claude direct: $2-3
- OpenRouter Claude: $2-3
- OpenRouter Qwen 72B: $0.30-0.50
- OpenRouter DeepSeek: $0.10-0.20
- Local 16GB GPU: $0 (electricity only!)

### Configuration

```yaml
ai:
  mode: openrouter  # Or hybrid

  openrouter:
    api_key: ${OPENROUTER_API_KEY}
    model: qwen/qwen-2.5-72b-instruct  # Cheap & good
    # or: deepseek/deepseek-coder  # Best for code
    # or: anthropic/claude-3.5-sonnet  # Highest quality
    max_tokens: 2000
    track_costs: true
    max_budget: 2.00
```

---

## Cost Analysis with 16GB GPU

### Scenario 1: Full Local (Recommended)
```
LLM: Qwen 14B (local)
Embeddings: mpnet (GPU)
Cost: $0 (only electricity ~$0.50)
Time: ~60-100 minutes
Quality: Excellent
```

### Scenario 2: Hybrid (Local + OpenRouter)
```
LLM: 90% Qwen 14B, 10% OpenRouter DeepSeek
Embeddings: mpnet (GPU)
Cost: ~$0.20
Time: ~70 minutes
Quality: Excellent
```

### Scenario 3: Hybrid (Local + Claude)
```
LLM: 80% Qwen 14B, 20% Claude API
Embeddings: mpnet (GPU)
Cost: ~$0.80
Time: ~65 minutes
Quality: Superior
```

### Scenario 4: OpenRouter Only
```
LLM: OpenRouter Qwen 72B
Embeddings: mpnet (GPU)
Cost: ~$0.40
Time: ~30 minutes (parallel API calls)
Quality: Excellent
```

---

## Recommended Configuration for Your Setup

Given your 16GB GPU, Ollama, LM Studio, and Docker:

```yaml
# config.yaml - RECOMMENDED SETUP

ai:
  mode: local_only  # Start here, upgrade to hybrid if needed

  local:
    provider: ollama
    model: qwen2.5:14b
    temperature: 0.3
    timeout: 120
    ollama:
      host: http://localhost:11434
      num_gpu: 1

embeddings:
  model: all-mpnet-base-v2
  device: cuda
  batch_size: 64
  gpu_id: 0
  precision: float16

clustering:
  similarity_threshold: 0.85

pipeline:
  parallel:
    enabled: true
    max_workers: 4  # Can process multiple clusters in parallel
```

**Why this setup:**
- ✓ Zero API costs
- ✓ Excellent quality (14B model)
- ✓ Fast embeddings (GPU)
- ✓ Reasonable speed (~90 min total)
- ✓ Privacy (all local)
- ✓ Can run offline

**If you need faster/better:**
Add OpenRouter fallback for complex cases (~$0.20 total cost)

---

## Troubleshooting

### GPU Not Detected

```bash
# Check PyTorch sees GPU
python -c "import torch; print(torch.cuda.is_available())"

# If False, reinstall PyTorch with correct CUDA version
pip uninstall torch torchvision
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

### Out of Memory (OOM)

**For Ollama:**
```bash
# Use smaller model or quantization
ollama pull qwen2.5:7b  # Instead of 14b

# Or use more aggressive quantization
ollama pull qwen2.5:14b-q4_K_M
```

**For Embeddings:**
```python
# Reduce batch size in config.yaml
batch_size: 32  # Instead of 64
```

### Slow Performance

```bash
# Check GPU utilization
nvidia-smi

# If GPU usage low:
# 1. Increase batch size
# 2. Check CUDA version matches
# 3. Use fp16 precision
```

---

## Next Steps

1. **Verify GPU setup:**
   ```bash
   cd dedup
   python -c "import torch; print(f'CUDA: {torch.cuda.is_available()}')"
   ```

2. **Pull recommended model:**
   ```bash
   ollama pull qwen2.5:14b
   ```

3. **Update config:**
   ```bash
   # Edit config.yaml
   # Set device: cuda
   # Set model: qwen2.5:14b
   ```

4. **Test setup:**
   ```bash
   make install
   # Run a test when pipeline is implemented
   ```

5. **Monitor during run:**
   ```bash
   # Terminal 1: Run pipeline
   python scripts/run_all.py

   # Terminal 2: Monitor GPU
   watch -n 0.5 nvidia-smi
   ```

---

## References

- [Ollama Models](https://ollama.ai/library)
- [LM Studio](https://lmstudio.ai/)
- [OpenRouter](https://openrouter.ai/)
- [sentence-transformers](https://www.sbert.net/)
- [vLLM](https://docs.vllm.ai/)

**Your 16GB GPU is perfect for this project - you can run everything locally with excellent quality!**
