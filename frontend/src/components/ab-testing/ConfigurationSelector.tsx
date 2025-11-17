import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { RAGConfig } from '../../../types/config';
import { useConfigStore } from '../../../stores/configStore';

interface ConfigurationSelectorProps {
  label: string;
  value: RAGConfig | null;
  onChange: (config: RAGConfig) => void;
}

export function ConfigurationSelector({
  label,
  value,
  onChange
}: ConfigurationSelectorProps) {
  const { config: defaultConfig, presets, loadPreset } = useConfigStore();
  const [showCustom, setShowCustom] = React.useState(false);

  const handlePresetSelect = (presetName: string) => {
    const preset = presets?.find((p: any) => p.name?.toLowerCase() === presetName.toLowerCase());
    if (preset) {
      loadPreset(preset as any);
      // The preset is loaded into the store, but we need to get the current config
      // For now, we'll use a simplified approach
      onChange(defaultConfig);
    }
  };

  if (!value) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>{label}</CardTitle>
          <CardDescription>Select a configuration</CardDescription>
        </CardHeader>
        <CardContent>
          <Button onClick={() => onChange(defaultConfig)}>
            Use Current Settings
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>{label}</CardTitle>
        <CardDescription>
          {showCustom ? 'Custom Configuration' : 'Select Preset or Custom'}
        </CardDescription>
      </CardHeader>
      <CardContent>
        {!showCustom ? (
          <div className="space-y-2">
            <div className="grid grid-cols-2 gap-2">
              {presets?.slice(0, 6).map((preset: any) => (
                <Button
                  key={preset.name}
                  variant="outline"
                  size="sm"
                  onClick={() => handlePresetSelect(preset.name)}
                  className="text-xs"
                >
                  {preset.name}
                </Button>
              ))}
            </div>
            <Button
              variant="outline"
              onClick={() => setShowCustom(true)}
              className="w-full"
            >
              Use Custom Configuration
            </Button>
          </div>
        ) : (
          <div className="space-y-2">
            <div className="text-sm space-y-1">
              <div><strong>Model:</strong> {value.model}</div>
              <div><strong>Top-K:</strong> {value.topK}</div>
              <div><strong>Context Window:</strong> {value.contextWindow}</div>
              <div><strong>Web Search:</strong> {value.useWebSearch ? 'Yes' : 'No'}</div>
              <div><strong>Reranking:</strong> {value.useReranking ? 'Yes' : 'No'}</div>
            </div>
            <Button
              variant="outline"
              onClick={() => setShowCustom(false)}
              className="w-full"
            >
              Select Preset Instead
            </Button>
          </div>
        )}

        {/* Configuration Preview */}
        {value && (
          <div className="mt-4 p-3 bg-muted rounded-md text-xs">
            <div className="font-semibold mb-1">Current Configuration:</div>
            <div className="space-y-1">
              <div>Model: {value.model}</div>
              <div>Top-K: {value.topK}</div>
              <div>Context: {value.contextWindow}</div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

