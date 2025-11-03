// Token Cost Estimation
// Based on typical LLM API pricing (for educational purposes)

export interface TokenCostEstimate {
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  estimated_cost_usd: number;
  model: string;
}

// Pricing per 1M tokens (approximate, for education)
const MODEL_PRICING = {
  // GPT-4 class (if using API)
  'gpt-4': { prompt: 30, completion: 60 },
  'gpt-4-turbo': { prompt: 10, completion: 30 },
  
  // GPT-3.5 class
  'gpt-3.5-turbo': { prompt: 0.5, completion: 1.5 },
  
  // Claude class  
  'claude-3-opus': { prompt: 15, completion: 75 },
  'claude-3-sonnet': { prompt: 3, completion: 15 },
  'claude-3-haiku': { prompt: 0.25, completion: 1.25 },
  
  // Local Ollama (free, but show hardware cost)
  'llama3.1:8b': { prompt: 0, completion: 0, note: 'Free (local)' },
  'llama3.2:3b': { prompt: 0, completion: 0, note: 'Free (local)' },
  'llama3.2:1b': { prompt: 0, completion: 0, note: 'Free (local)' },
  'mistral': { prompt: 0, completion: 0, note: 'Free (local)' },
  
  // Default for unknown models
  'default': { prompt: 2, completion: 6, note: 'Estimated' },
};

export function estimateTokenCost(
  promptTokens: number,
  completionTokens: number,
  model: string
): TokenCostEstimate {
  // Normalize model name
  const modelKey = Object.keys(MODEL_PRICING).find(key => 
    model.toLowerCase().includes(key.toLowerCase())
  ) || 'default';
  
  const pricing = MODEL_PRICING[modelKey as keyof typeof MODEL_PRICING];
  
  // Calculate cost (pricing is per 1M tokens, so divide by 1,000,000)
  const promptCost = (promptTokens / 1_000_000) * pricing.prompt;
  const completionCost = (completionTokens / 1_000_000) * pricing.completion;
  const totalCost = promptCost + completionCost;
  
  return {
    prompt_tokens: promptTokens,
    completion_tokens: completionTokens,
    total_tokens: promptTokens + completionTokens,
    estimated_cost_usd: totalCost,
    model: modelKey,
  };
}

export function formatCost(cost: number): string {
  if (cost === 0) return 'Free (local)';
  if (cost < 0.01) return `< $0.01`;
  return `$${cost.toFixed(4)}`;
}

export function calculateMonthlyCost(
  queriesPerDay: number,
  avgPromptTokens: number,
  avgCompletionTokens: number,
  model: string
): { daily: number; monthly: number; yearly: number } {
  const costPerQuery = estimateTokenCost(avgPromptTokens, avgCompletionTokens, model);
  
  return {
    daily: costPerQuery.estimated_cost_usd * queriesPerDay,
    monthly: costPerQuery.estimated_cost_usd * queriesPerDay * 30,
    yearly: costPerQuery.estimated_cost_usd * queriesPerDay * 365,
  };
}

// Hardware cost estimation (for Ollama)
export interface HardwareCost {
  gpu_type: string;
  hourly_rate: number;
  monthly_rate: number;
}

export const HARDWARE_COSTS: { [key: string]: HardwareCost } = {
  'laptop-m2': {
    gpu_type: 'Mac M2 (local)',
    hourly_rate: 0, // Already owned
    monthly_rate: 0,
  },
  'laptop-m3': {
    gpu_type: 'Mac M3 (local)',
    hourly_rate: 0,
    monthly_rate: 0,
  },
  'aws-t4': {
    gpu_type: 'AWS g4dn.xlarge (T4)',
    hourly_rate: 0.526,
    monthly_rate: 380, // 24/7
  },
  'aws-a10g': {
    gpu_type: 'AWS g5.xlarge (A10G)',
    hourly_rate: 1.006,
    monthly_rate: 727,
  },
  'aws-a100': {
    gpu_type: 'AWS p4d.24xlarge (A100)',
    hourly_rate: 32.77,
    monthly_rate: 23676,
  },
};

export function getHardwareCostEstimate(
  model: string,
  queriesPerDay: number
): { model: string; recommendation: HardwareCost; reasoning: string } {
  // Recommend hardware based on model size
  if (model.includes('1b') || model.includes('3b')) {
    return {
      model,
      recommendation: HARDWARE_COSTS['laptop-m2'],
      reasoning: 'Small models run well on laptops (M2/M3)',
    };
  }
  
  if (model.includes('7b') || model.includes('8b')) {
    if (queriesPerDay < 100) {
      return {
        model,
        recommendation: HARDWARE_COSTS['laptop-m3'],
        reasoning: 'Low volume: laptop OK for development',
      };
    } else {
      return {
        model,
        recommendation: HARDWARE_COSTS['aws-t4'],
        reasoning: 'Medium volume: GPU instance recommended',
      };
    }
  }
  
  return {
    model,
    recommendation: HARDWARE_COSTS['aws-a10g'],
    reasoning: 'Large models need GPU acceleration',
  };
}

