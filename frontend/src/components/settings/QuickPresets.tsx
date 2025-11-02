import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '../../services/api';
import { useConfigStore } from '../../stores/configStore';
import { Button } from '../ui/button';
import { Card, CardContent } from '../ui/card';
import { Zap } from 'lucide-react';

export function QuickPresets() {
  const loadPreset = useConfigStore((state) => state.loadPreset);

  const { data: presets, isLoading } = useQuery({
    queryKey: ['presets'],
    queryFn: () => api.getPresets(),
  });

  if (isLoading || !presets) {
    return null;
  }

  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-sm font-medium mb-1">Quick Presets</h3>
        <p className="text-xs text-muted-foreground">
          Load predefined configurations
        </p>
      </div>

      <div className="grid grid-cols-2 gap-3">
        {presets.map((preset: any) => (
          <Card
            key={preset.name}
            className="cursor-pointer hover:border-primary transition-colors"
            onClick={() => loadPreset(preset)}
          >
            <CardContent className="p-4">
              <div className="flex items-start gap-2 mb-2">
                <Zap className="h-4 w-4 text-primary mt-0.5" />
                <div className="flex-1">
                  <h4 className="text-sm font-semibold capitalize">
                    {preset.name}
                  </h4>
                  <p className="text-xs text-muted-foreground mt-1">
                    {preset.description}
                  </p>
                  {preset.expected_metrics && (
                    <p className="text-xs text-primary mt-1">
                      {preset.expected_metrics.latency}
                    </p>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

