import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { api } from '@/services/api';
import { useQuery } from '@tanstack/react-query';
import { Activity, Zap, Cpu, Thermometer } from 'lucide-react';

interface GPUMetric {
  timestamp: number;
  utilization?: number;
  memory_percent?: number;
  power_watts?: number;
  temperature?: number;
}

interface GPUData {
  name: string;
  index: string;
  history: GPUMetric[];
}

export function GPUMonitoringPage() {
  const [gpuData, setGpuData] = useState<Map<string, GPUData>>(new Map());
  const [maxHistoryLength] = useState(60); // Keep last 60 data points (5 minutes at 5s intervals)

  // Poll GPU metrics every 5 seconds
  const { data: metricsResponse } = useQuery({
    queryKey: ['gpu-metrics'],
    queryFn: () => api.getGPUMetrics(),
    refetchInterval: 5000, // Poll every 5 seconds
    retry: 1,
  });

  useEffect(() => {
    if (metricsResponse?.success && metricsResponse.gpus) {
      setGpuData((prev) => {
        const newData = new Map(prev);

        metricsResponse.gpus.forEach((gpu) => {
          const existing = newData.get(gpu.index) || {
            name: gpu.name,
            index: gpu.index,
            history: [],
          };

          // Add new data point
          const newPoint: GPUMetric = {
            timestamp: metricsResponse.timestamp,
            utilization: gpu.utilization,
            memory_percent: gpu.memory_percent,
            power_watts: gpu.power_watts,
            temperature: gpu.temperature,
          };

          existing.history = [...existing.history, newPoint];

          // Keep only last N points
          if (existing.history.length > maxHistoryLength) {
            existing.history = existing.history.slice(-maxHistoryLength);
          }

          newData.set(gpu.index, existing);
        });

        return newData;
      });
    }
  }, [metricsResponse, maxHistoryLength]);

  // Format timestamp for display
  const formatTime = (timestamp: number) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString();
  };

  // Prepare chart data
  const getChartData = (gpu: GPUData) => {
    return gpu.history.map((point) => ({
      time: formatTime(point.timestamp),
      timestamp: point.timestamp,
      utilization: point.utilization ?? 0,
      memory: point.memory_percent ?? 0,
      power: point.power_watts ?? 0,
      temperature: point.temperature ?? 0,
    }));
  };

  const gpus = Array.from(gpuData.values());

  return (
    <div className="container mx-auto px-6 py-8 max-w-7xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">GPU Monitoring</h1>
        <p className="text-muted-foreground">
          Real-time GPU metrics: Utilization, Memory, and Power Consumption
        </p>
      </div>

      {!metricsResponse?.success && (
        <Card className="mb-6">
          <CardContent className="p-6">
            <div className="text-center text-muted-foreground">
              {metricsResponse?.error || 'Loading GPU metrics...'}
            </div>
          </CardContent>
        </Card>
      )}

      {gpus.length === 0 && metricsResponse?.success && (
        <Card className="mb-6">
          <CardContent className="p-6">
            <div className="text-center text-muted-foreground">
              No GPUs detected. Make sure nvidia-exporter is running and GPUs are available.
            </div>
          </CardContent>
        </Card>
      )}

      {gpus.map((gpu) => {
        const chartData = getChartData(gpu);
        const latest = gpu.history[gpu.history.length - 1];

        return (
          <div key={gpu.index} className="mb-6 space-y-4">
            {/* GPU Header with Current Stats */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Activity className="h-5 w-5" />
                  {gpu.name} (GPU {gpu.index})
                </CardTitle>
                <CardDescription>Real-time GPU performance metrics</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                  <div className="flex items-center gap-3 p-4 bg-muted rounded-lg">
                    <Cpu className="h-8 w-8 text-blue-500" />
                    <div>
                      <div className="text-sm text-muted-foreground">GPU Utilization</div>
                      <div className="text-2xl font-bold">
                        {latest?.utilization?.toFixed(1) ?? 'N/A'}%
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3 p-4 bg-muted rounded-lg">
                    <Zap className="h-8 w-8 text-yellow-500" />
                    <div>
                      <div className="text-sm text-muted-foreground">Memory Usage</div>
                      <div className="text-2xl font-bold">
                        {latest?.memory_percent?.toFixed(1) ?? 'N/A'}%
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3 p-4 bg-muted rounded-lg">
                    <Zap className="h-8 w-8 text-green-500" />
                    <div>
                      <div className="text-sm text-muted-foreground">Power Draw</div>
                      <div className="text-2xl font-bold">
                        {latest?.power_watts?.toFixed(1) ?? 'N/A'}W
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3 p-4 bg-muted rounded-lg">
                    <Thermometer className="h-8 w-8 text-red-500" />
                    <div>
                      <div className="text-sm text-muted-foreground">Temperature</div>
                      <div className="text-2xl font-bold">
                        {latest?.temperature?.toFixed(1) ?? 'N/A'}°C
                      </div>
                    </div>
                  </div>
                </div>

                {/* Combined Chart */}
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg">Performance Over Time</CardTitle>
                    <CardDescription>
                      Last {gpu.history.length} data points (updates every 5 seconds)
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    {chartData.length > 0 ? (
                      <ResponsiveContainer width="100%" height={400}>
                        <LineChart data={chartData}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis
                            dataKey="time"
                            tick={{ fontSize: 12 }}
                            interval={Math.floor(chartData.length / 10)} // Show ~10 labels
                          />
                          <YAxis yAxisId="percent" domain={[0, 100]} label={{ value: '%', angle: -90, position: 'insideLeft' }} />
                          <YAxis yAxisId="watts" orientation="right" label={{ value: 'Watts', angle: 90, position: 'insideRight' }} />
                          <Tooltip
                            labelFormatter={(label) => `Time: ${label}`}
                            formatter={(value: number, name: string) => {
                              if (name === 'utilization' || name === 'memory') {
                                return [`${value.toFixed(1)}%`, name === 'utilization' ? 'GPU %' : 'Memory %'];
                              } else if (name === 'power') {
                                return [`${value.toFixed(1)}W`, 'Power'];
                              } else if (name === 'temperature') {
                                return [`${value.toFixed(1)}°C`, 'Temp'];
                              }
                              return [value, name];
                            }}
                          />
                          <Legend />
                          <Line
                            yAxisId="percent"
                            type="monotone"
                            dataKey="utilization"
                            stroke="#3b82f6"
                            strokeWidth={2}
                            name="GPU %"
                            dot={false}
                            activeDot={{ r: 4 }}
                          />
                          <Line
                            yAxisId="percent"
                            type="monotone"
                            dataKey="memory"
                            stroke="#eab308"
                            strokeWidth={2}
                            name="Memory %"
                            dot={false}
                            activeDot={{ r: 4 }}
                          />
                          <Line
                            yAxisId="watts"
                            type="monotone"
                            dataKey="power"
                            stroke="#22c55e"
                            strokeWidth={2}
                            name="Power (W)"
                            dot={false}
                            activeDot={{ r: 4 }}
                          />
                        </LineChart>
                      </ResponsiveContainer>
                    ) : (
                      <div className="h-96 flex items-center justify-center text-muted-foreground">
                        Collecting data... Please wait a few seconds.
                      </div>
                    )}
                  </CardContent>
                </Card>
              </CardContent>
            </Card>
          </div>
        );
      })}
    </div>
  );
}

