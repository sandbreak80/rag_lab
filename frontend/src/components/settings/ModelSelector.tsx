import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '../../services/api';
import { useConfigStore } from '../../stores/configStore';
import { Select } from '../ui/select';
import { Label } from '../ui/label';

export function ModelSelector() {
  const model = useConfigStore((state) => state.model);
  const setModel = useConfigStore((state) => state.setModel);

  const { data: modelsData, isLoading } = useQuery({
    queryKey: ['models'],
    queryFn: () => api.getModels(),
  });

  const models = modelsData?.models || [];

  return (
    <div className="space-y-2">
      <Label htmlFor="model-select">LLM Model</Label>
      <Select
        id="model-select"
        value={model}
        onChange={(e) => setModel(e.target.value)}
        disabled={isLoading}
      >
        {isLoading ? (
          <option>Loading models...</option>
        ) : models.length === 0 ? (
          <option>No models available</option>
        ) : (
          models.map((m: any) => (
            <option key={m.name} value={m.name}>
              {m.name} ({m.details?.parameter_size || 'Unknown size'})
            </option>
          ))
        )}
      </Select>
      <p className="text-xs text-muted-foreground">
        Choose the LLM model for generating responses
      </p>
    </div>
  );
}

