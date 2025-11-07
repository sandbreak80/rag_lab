# GPU Compatibility Guide for RAG Lab

**Complete guide to choosing the right AWS EC2 GPU instance**

---

## 🎯 Quick Answer

**For vLLM (Recommended for Production):**
- ✅ **g5.2xlarge** - NVIDIA A10G (Ampere architecture)
- ✅ **g5.xlarge** - Smaller, still supports vLLM
- ✅ **p3.2xlarge** - NVIDIA V100 (Volta, works but expensive)

**For Ollama Only (Development/Cost-Sensitive):**
- ✅ **g4dn.2xlarge** - NVIDIA T4 (Turing, no vLLM)
- ✅ **g4dn.xlarge** - Smaller T4

---

## 📊 Detailed Comparison

### Instance Type Comparison

| Instance | GPU | Arch | VRAM | vCPU | RAM | vLLM | Cost/hr | Cost/day | Best For |
|----------|-----|------|------|------|-----|------|---------|----------|----------|
| **g5.2xlarge** | A10G | Ampere | 24GB | 8 | 32GB | ✅ YES | $1.21 | $29 | Production vLLM |
| **g5.xlarge** | A10G | Ampere | 24GB | 4 | 16GB | ✅ YES | $1.01 | $24 | Dev vLLM |
| **g4dn.2xlarge** | T4 | Turing | 16GB | 8 | 32GB | ❌ NO | $0.75 | $18 | Ollama only |
| **g4dn.xlarge** | T4 | Turing | 16GB | 4 | 16GB | ❌ NO | $0.53 | $13 | Small Ollama |
| **p3.2xlarge** | V100 | Volta | 16GB | 8 | 61GB | ✅ YES | $3.06 | $73 | ML training |

---

## 🔍 Why vLLM Support Matters

### What is vLLM?

vLLM is a fast and efficient library for LLM inference with:
- **PagedAttention** - 24x faster than HuggingFace
- **Continuous batching** - Higher throughput
- **Tensor parallelism** - Multi-GPU support
- **OpenAI-compatible API** - Drop-in replacement

### GPU Architecture Requirements

| Architecture | Generation | vLLM Support | Examples |
|--------------|-----------|--------------|----------|
| **Ampere** | 2020 | ✅ YES | A10G, A100 |
| **Volta** | 2017 | ✅ YES | V100 |
| **Turing** | 2018 | ❌ NO | T4 |
| **Pascal** | 2016 | ❌ NO | P100 |

**Key Point:** vLLM requires **Compute Capability 7.0+** (Volta/Ampere), T4 is only 7.5 but lacks required features.

---

## 💰 Cost Analysis

### Monthly Costs (24/7 Operation)

| Instance | Running 24/7 | Stopped | Savings |
|----------|--------------|---------|---------|
| g5.2xlarge | $870/month | $20/month | 98% |
| g5.xlarge | $727/month | $10/month | 99% |
| g4dn.2xlarge | $540/month | $20/month | 96% |
| g4dn.xlarge | $382/month | $10/month | 97% |

### Cost Optimization Strategies

#### 1. Stop When Not Using (Biggest Savings)
```bash
# Stop instance (keeps EBS, only pay storage)
aws ec2 stop-instances --instance-ids i-xxxxx

# Savings: 96-99% reduction!
```

#### 2. Scheduled Operation (Business Hours)
```
8am-6pm weekdays = 50 hours/week
- g5.2xlarge: $242/month (72% savings)
- g4dn.2xlarge: $150/month (72% savings)
```

#### 3. Spot Instances (70% Discount)
```bash
# Launch as spot instance
--instance-market-options '{"MarketType":"spot"}'

# Savings:
- g5.2xlarge spot: ~$0.36/hour (70% off)
- g4dn.2xlarge spot: ~$0.23/hour (70% off)

# Risk: Can be interrupted if AWS needs capacity
```

#### 4. Reserved Instances (1-3 year commitment)
```
1-year reserved:
- g5.2xlarge: ~$0.72/hour (40% savings)
- g4dn.2xlarge: ~$0.45/hour (40% savings)
```

---

## 🚀 Performance Comparison

### Inference Speed (Tokens/Second)

| Model | T4 (g4dn) | A10G (g5) | Speedup |
|-------|-----------|-----------|---------|
| Llama-2-7B | ~25 tok/s | ~40 tok/s | 1.6x |
| Llama-2-13B | ~12 tok/s | ~20 tok/s | 1.7x |
| Mistral-7B | ~28 tok/s | ~45 tok/s | 1.6x |

**Note:** These are approximate. vLLM on A10G is typically 50-100% faster than Ollama on T4.

### Maximum Model Size

| GPU | VRAM | Max Model Size | Examples |
|-----|------|----------------|----------|
| T4 | 16GB | ~7B parameters | Llama-2-7B, Mistral-7B |
| A10G | 24GB | ~13B parameters | Llama-2-13B, Mixtral-8x7B (quantized) |

---

## 🎯 Decision Matrix

### Choose **g5.2xlarge** (A10G) if you need:
- ✅ vLLM support (fastest inference)
- ✅ Larger models (13B parameters)
- ✅ Production deployment
- ✅ OpenAI-compatible API
- ✅ Multi-user concurrent access
- ✅ Best performance/cost ratio for production

### Choose **g4dn.2xlarge** (T4) if you need:
- ✅ Ollama only (no vLLM)
- ✅ Smaller models (7B and under)
- ✅ Development/testing
- ✅ Lowest cost option
- ✅ Simple single-user access

---

## 🛠️ Quick Start for Each Instance Type

### For g5.2xlarge (vLLM + Ollama)

```bash
cd rag_lab/aws/scripts
./launch-g5-vllm.sh
```

**What you get:**
- vLLM (native, fast inference)
- Ollama (Docker, for compatibility)
- RAG Lab (all services)
- Setup time: 15-20 minutes

### For g4dn.2xlarge (Ollama Only)

```bash
cd rag_lab/aws/scripts
./aws-launch-rag-lab.sh
```

**What you get:**
- Ollama (Docker)
- RAG Lab (all services)
- Setup time: 10-15 minutes

---

## 🔧 Technical Details

### CUDA and Driver Requirements

| GPU | CUDA Version | Min Driver | Recommended |
|-----|--------------|------------|-------------|
| A10G | 11.1+ | 450.80+ | 535+ |
| T4 | 10.0+ | 410.48+ | 535+ |

**Cloud-init scripts automatically install latest drivers**

### Memory Considerations

**T4 (16GB VRAM):**
```
Model Size | Status
-----------+--------
7B         | ✅ Good (uses ~10GB)
13B        | ⚠️ Tight (uses ~15GB, may OOM)
20B+       | ❌ Too large
```

**A10G (24GB VRAM):**
```
Model Size | Status
-----------+--------
7B         | ✅ Excellent (room for batch processing)
13B        | ✅ Good (uses ~18GB)
20B        | ⚠️ Tight (quantization needed)
70B        | ❌ Too large (need multi-GPU)
```

---

## 📝 vLLM Setup Details

### Installation (Automatic in cloud-init)

```bash
# Native Python installation (faster than Docker)
python3 -m venv /home/ubuntu/vllm-env
source /home/ubuntu/vllm-env/bin/activate
pip install vllm
```

### Starting vLLM Server

```bash
# Option 1: Systemd service
sudo systemctl start vllm
sudo systemctl status vllm

# Option 2: Manual start
source /home/ubuntu/vllm-env/bin/activate
python -m vllm.entrypoints.openai.api_server \
    --model /home/ubuntu/models/llama-2-7b-chat \
    --host 0.0.0.0 \
    --port 8001
```

### Testing vLLM API

```bash
# List models
curl http://localhost:8001/v1/models

# Test completion
curl http://localhost:8001/v1/completions \
    -H "Content-Type: application/json" \
    -d '{
        "model": "llama-2-7b-chat",
        "prompt": "What is AI?",
        "max_tokens": 100
    }'

# Chat completion (OpenAI-compatible)
curl http://localhost:8001/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d '{
        "model": "llama-2-7b-chat",
        "messages": [
            {"role": "user", "content": "Explain RAG"}
        ]
    }'
```

---

## 🔄 Migration Guide

### From g4dn (T4) to g5 (A10G)

```bash
# 1. Create snapshot of g4dn EBS volume
aws ec2 create-snapshot --volume-id vol-xxxxx

# 2. Launch g5 instance with vLLM
./launch-g5-vllm.sh

# 3. (Optional) Restore data from snapshot
# Attach snapshot as secondary volume to g5 instance

# 4. Test vLLM
ssh -i key.pem ubuntu@g5-ip
/home/ubuntu/test-vllm.sh

# 5. Terminate g4dn instance
aws ec2 terminate-instances --instance-ids i-xxxxx-g4dn
```

---

## 🎓 Best Practices

### Development Workflow
1. **Development:** Use g4dn.xlarge with Ollama ($13/day)
2. **Testing:** Use g5.xlarge with vLLM ($24/day)
3. **Production:** Use g5.2xlarge with vLLM ($29/day)
4. **Always:** Stop instances when not in use

### Model Selection
- **Development:** Use 7B models (Llama-2-7B, Mistral-7B)
- **Production:** Use 13B models if quality needed
- **Quantization:** Use 4-bit quantization to fit larger models

### Cost Control
- **Tag instances** with auto-stop schedules
- **Use CloudWatch alarms** for cost monitoring
- **Set billing alerts** at $50, $100, $200
- **Stop daily** if not in continuous use

---

## 📊 Real-World Scenarios

### Scenario 1: Solo Developer Learning RAG
**Recommendation:** g4dn.xlarge with Ollama
- Cost: $13/day, $382/month if 24/7
- Reality: Stop when done = $1-2/day actual
- Models: Llama-2-7B, Mistral-7B
- **Monthly cost: $30-60**

### Scenario 2: Team Building Production System
**Recommendation:** g5.2xlarge with vLLM
- Cost: $29/day running
- Use: Business hours (10hr/day) = $12/day
- Models: Llama-2-13B for quality
- **Monthly cost: $360**

### Scenario 3: Demo/Presentation
**Recommendation:** g5.2xlarge, stop after demo
- Launch 1 hour before demo
- Run demo (2-3 hours)
- Stop immediately after
- **Cost per demo: $5-10**

---

## ❓ FAQ

### Q: Can I use vLLM on T4?
**A:** No. T4 uses Turing architecture which lacks required features for vLLM. You must use Volta (V100) or Ampere (A10G, A100) GPUs.

### Q: Is g5 worth the 60% higher cost?
**A:** Yes, if you need:
- vLLM (2x faster inference)
- Larger models (13B+)
- Production deployment
- Better user experience

### Q: Can I switch between Ollama and vLLM?
**A:** Yes! Both are installed on g5 instances. Use Ollama for compatibility, vLLM for speed.

### Q: What about g5.xlarge vs g5.2xlarge?
**A:** g5.xlarge has:
- Same GPU (A10G, 24GB)
- Half the vCPUs (4 vs 8)
- Half the RAM (16GB vs 32GB)
- $0.20/hour cheaper
- Fine for single-user, smaller RAG Lab

### Q: Spot instances reliable enough?
**A:** For development: Yes
- 70% cost savings
- Interruptions rare with g5/g4dn
- Can request spot with max price

For production: No
- Use on-demand or reserved instances
- Spot interruptions disruptive

---

## 🔗 Additional Resources

- [AWS G5 Instances](https://aws.amazon.com/ec2/instance-types/g5/)
- [AWS G4 Instances](https://aws.amazon.com/ec2/instance-types/g4/)
- [vLLM Documentation](https://docs.vllm.ai/)
- [NVIDIA A10G Spec Sheet](https://www.nvidia.com/en-us/data-center/products/a10-gpu/)
- [NVIDIA T4 Spec Sheet](https://www.nvidia.com/en-us/data-center/tesla-t4/)

---

## ✅ Summary

**For RAG Lab:**
- **Learning/Dev:** g4dn.xlarge ($13/day) - Ollama only
- **Testing:** g5.xlarge ($24/day) - vLLM supported
- **Production:** g5.2xlarge ($29/day) - Best performance

**Key Takeaway:** g5 (A10G) supports vLLM, g4dn (T4) does not. The 60% cost increase pays for itself with 2x faster inference and support for larger models.

**Stop instances when not using to save 96-99%!**

---

*Last updated: November 6, 2025*

