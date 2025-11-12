import React from 'react';
import { Card, CardContent } from '../ui/card';
import { Clock, Zap, AlertCircle } from 'lucide-react';

interface StageTimings {
    vector_ms?: number;
    web_ms?: number;
    llm_ms?: number;
    total_ms?: number;
    retrieve_parallel_ms?: number;
    web_skipped?: boolean;
    web_reason?: 'disabled' | 'early_stop' | 'timeout' | 'ok';
    web_enabled?: boolean;
}

interface StageTimingsDisplayProps {
    timings: StageTimings;
    compact?: boolean;
}

export function StageTimingsDisplay({ timings, compact = false }: StageTimingsDisplayProps) {
    if (!timings || !timings.total_ms) {
        return (
            <div className="p-4 text-center text-muted-foreground text-sm">
                No timing data available
            </div>
        );
    }

    const formatMs = (ms?: number) => {
        if (ms === undefined || ms === null) return 'N/A';
        return `${ms.toFixed(0)}ms`;
    };

    const getWebBadge = () => {
        if (!timings.web_skipped) {
            return null; // Web ran successfully
        }

        const badgeConfig = {
            disabled: { color: 'bg-gray-500/20 text-gray-700 dark:text-gray-300', text: 'Web Skipped (Disabled)' },
            early_stop: { color: 'bg-amber-500/20 text-amber-700 dark:text-amber-300', text: 'Web Skipped (Early-stop)' },
            timeout: { color: 'bg-red-500/20 text-red-700 dark:text-red-300', text: 'Web Timed Out' },
        };

        const config = badgeConfig[timings.web_reason || 'disabled'];

        return (
            <span
                className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium ${config.color}`}
                data-testid="metrics-web-skipped-badge"
                data-reason={timings.web_reason}
            >
                <AlertCircle className="h-3 w-3" />
                {config.text}
            </span>
        );
    };

    if (compact) {
        return (
            <div className="flex flex-wrap gap-2 text-xs" data-testid="perf-breakdown">
                {timings.vector_ms !== undefined && (
                    <span className="inline-flex items-center gap-1 px-2 py-1 bg-red-500/10 text-red-700 dark:text-red-300 rounded" data-testid="perf-vector-ms">
                        <Clock className="h-3 w-3" />
                        Vector: {formatMs(timings.vector_ms)}
                    </span>
                )}
                {timings.web_ms !== undefined && (
                    <span className="inline-flex items-center gap-1 px-2 py-1 bg-blue-500/10 text-blue-700 dark:text-blue-300 rounded" data-testid="perf-web-ms">
                        <Clock className="h-3 w-3" />
                        Web: {formatMs(timings.web_ms)}
                    </span>
                )}
                {timings.llm_ms !== undefined && (
                    <span className="inline-flex items-center gap-1 px-2 py-1 bg-indigo-500/10 text-indigo-700 dark:text-indigo-300 rounded" data-testid="perf-llm-ms">
                        <Clock className="h-3 w-3" />
                        LLM: {formatMs(timings.llm_ms)}
                    </span>
                )}
                {timings.total_ms !== undefined && (
                    <span className="inline-flex items-center gap-1 px-2 py-1 bg-primary/10 text-primary rounded font-medium" data-testid="perf-total-ms">
                        <Zap className="h-3 w-3" />
                        Total: {formatMs(timings.total_ms)}
                    </span>
                )}
                {timings.retrieve_parallel_ms !== undefined && (
                    <span className="inline-flex items-center gap-1 px-2 py-1 bg-green-500/10 text-green-700 dark:text-green-300 rounded" data-testid="perf-parallel-ms">
                        <Zap className="h-3 w-3" />
                        Parallel: {formatMs(timings.retrieve_parallel_ms)}
                    </span>
                )}
                {getWebBadge()}
            </div>
        );
    }

    return (
        <div className="grid grid-cols-2 gap-4" data-testid="perf-breakdown">
            {/* Vector Search */}
            {timings.vector_ms !== undefined && (
                <Card>
                    <CardContent className="p-4">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-muted-foreground">Vector Search</p>
                                <p className="text-2xl font-bold" data-testid="metrics-vector-ms">{formatMs(timings.vector_ms)}</p>
                            </div>
                            <div className="h-12 w-12 rounded-full bg-red-500/10 flex items-center justify-center">
                                <Clock className="h-6 w-6 text-red-500" />
                            </div>
                        </div>
                    </CardContent>
                </Card>
            )}

            {/* Web Search */}
            {timings.web_ms !== undefined && (
                <Card>
                    <CardContent className="p-4">
                        <div className="flex items-center justify-between">
                            <div className="flex-1">
                                <p className="text-sm text-muted-foreground">Web Search</p>
                                <p className="text-2xl font-bold" data-testid="metrics-web-ms">{formatMs(timings.web_ms)}</p>
                                {getWebBadge()}
                            </div>
                            <div className="h-12 w-12 rounded-full bg-blue-500/10 flex items-center justify-center">
                                <Clock className="h-6 w-6 text-blue-500" />
                            </div>
                        </div>
                    </CardContent>
                </Card>
            )}

            {/* LLM Generation */}
            {timings.llm_ms !== undefined && (
                <Card>
                    <CardContent className="p-4">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-muted-foreground">LLM Generation</p>
                                <p className="text-2xl font-bold" data-testid="metrics-llm-ms">{formatMs(timings.llm_ms)}</p>
                            </div>
                            <div className="h-12 w-12 rounded-full bg-indigo-500/10 flex items-center justify-center">
                                <Clock className="h-6 w-6 text-indigo-500" />
                            </div>
                        </div>
                    </CardContent>
                </Card>
            )}

            {/* Total */}
            {timings.total_ms !== undefined && (
                <Card className="border-primary">
                    <CardContent className="p-4">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-muted-foreground">Total Latency</p>
                                <p className="text-2xl font-bold text-primary" data-testid="metrics-total-ms">{formatMs(timings.total_ms)}</p>
                            </div>
                            <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center">
                                <Zap className="h-6 w-6 text-primary" />
                            </div>
                        </div>
                    </CardContent>
                </Card>
            )}

            {/* Parallel Retrieval (if present) */}
            {timings.retrieve_parallel_ms !== undefined && (
                <Card className="col-span-2">
                    <CardContent className="p-4">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-muted-foreground">Parallel Retrieval Speedup</p>
                                <p className="text-2xl font-bold text-green-600" data-testid="metrics-retrieve-parallel-ms">
                                    {formatMs(timings.retrieve_parallel_ms)}
                                </p>
                                <p className="text-xs text-muted-foreground mt-1">
                                    Vector + Web ran in parallel
                                </p>
                            </div>
                            <div className="h-12 w-12 rounded-full bg-green-500/10 flex items-center justify-center">
                                <Zap className="h-6 w-6 text-green-500" />
                            </div>
                        </div>
                    </CardContent>
                </Card>
            )}
        </div>
    );
}
