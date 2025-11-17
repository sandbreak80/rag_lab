import React, { useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '../../services/api';
import { useConfigStore } from '../../stores/configStore';
import { Button } from '../ui/button';
import { Card, CardContent } from '../ui/card';
import { Zap, Check } from 'lucide-react';

export function QuickPresets() {
  const loadPreset = useConfigStore((state) => state.loadPreset);
  const currentPreset = useConfigStore((state) => state.currentPreset);

  const { data: presets, isLoading } = useQuery({
    queryKey: ['presets'],
    queryFn: () => api.getPresets(),
  });

  // Auto-load "balanced" preset on first visit (when no preset is selected)
  useEffect(() => {
    if (!isLoading && presets && !currentPreset) {
      const balancedPreset = presets.find((p: any) => p.name === 'balanced' || p.name === 'Balanced (Recommended)');
      if (balancedPreset) {
        console.log('🎯 Auto-loading Balanced preset on first visit');
        // loadPreset expects the full preset object from API (with config, llm_config, etc.)
        loadPreset(balancedPreset as any);
      }
    }
  }, [isLoading, presets, currentPreset, loadPreset]);

  if (isLoading || !presets) {
    return null;
  }

  return (
    <div className="space-y-4">
      {/* Currently Active Preset Indicator */}
      {currentPreset && (
        <div
          className="flex items-center gap-2 px-3 py-2 bg-primary/10 border border-primary/30 rounded-lg"
          data-testid="preset-selected"
          data-preset-name={currentPreset}
        >
          <Check className="h-4 w-4 text-primary flex-shrink-0" />
          <div className="flex-1">
            <span className="text-sm font-medium text-primary">
              Currently Active:
            </span>
            <span className="text-sm font-semibold text-primary capitalize ml-1">
              {currentPreset}
            </span>
          </div>
        </div>
      )}

      <div className="grid grid-cols-2 gap-3">
        {presets.map((preset: any) => {
          const isSelected = currentPreset === preset.name;
          return (
            <Card
              key={preset.name}
              className={`cursor-pointer transition-all ${
                isSelected
                  ? 'border-primary bg-primary/5 ring-2 ring-primary/20 shadow-md'
                  : 'hover:border-primary hover:shadow-sm'
              }`}
              onClick={() => loadPreset(preset)}
              data-testid={`preset-card-${preset.name}`}
              data-selected={isSelected}
            >
              <CardContent className="p-4">
                <div className="flex items-start gap-2">
                  {isSelected ? (
                    <Check className="h-5 w-5 text-primary mt-0.5 flex-shrink-0" />
                  ) : (
                    <Zap className="h-5 w-5 text-muted-foreground mt-0.5 flex-shrink-0" />
                  )}
                  <div className="flex-1 min-w-0">
                    <h4 className={`text-sm font-semibold capitalize mb-1 ${
                      isSelected ? 'text-primary' : 'text-foreground'
                    }`}>
                      {preset.name}
                    </h4>
                    <p className="text-xs text-muted-foreground line-clamp-2">
                      {preset.description}
                    </p>
                    {preset.expected_metrics && (
                      <p className={`text-xs mt-1 font-medium ${
                        isSelected ? 'text-primary' : 'text-muted-foreground'
                      }`}>
                        ⚡ {preset.expected_metrics.latency}
                      </p>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}

