import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Trophy, Award } from 'lucide-react';

interface AutoGraderResultsProps {
  graderResult: any;
  winner?: string;
}

export function AutoGraderResults({
  graderResult,
  winner
}: AutoGraderResultsProps) {
  if (!graderResult) return null;

  const { response_a, response_b, explanation } = graderResult;

  const dimensions = [
    'answer_quality',
    'relevance',
    'faithfulness',
    'completeness',
    'conciseness',
    'source_quality'
  ];

  const dimensionLabels: Record<string, string> = {
    answer_quality: 'Answer Quality',
    relevance: 'Relevance',
    faithfulness: 'Faithfulness',
    completeness: 'Completeness',
    conciseness: 'Conciseness',
    source_quality: 'Source Quality'
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Award className="h-5 w-5" />
          Auto-Grader Results
          {winner && (
            <span className={`ml-auto px-3 py-1 rounded-full text-sm font-semibold ${
              winner === 'A' ? 'bg-green-100 text-green-800' :
              winner === 'B' ? 'bg-blue-100 text-blue-800' :
              'bg-gray-100 text-gray-800'
            }`}>
              {winner === 'tie' ? 'Tie' : `Winner: ${winner}`}
            </span>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-6">
          {/* Dimension Scores */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h4 className="font-semibold mb-3">Configuration A Scores</h4>
              <div className="space-y-2">
                {dimensions.map((dim) => (
                  <div key={dim} className="flex items-center justify-between">
                    <span className="text-sm">{dimensionLabels[dim]}:</span>
                    <div className="flex items-center gap-2">
                      <div className="w-32 bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-blue-600 h-2 rounded-full"
                          style={{ width: `${(response_a?.scores?.[dim] || 0) * 100}%` }}
                        />
                      </div>
                      <span className="text-sm font-medium w-12 text-right">
                        {(response_a?.scores?.[dim] || 0).toFixed(2)}
                      </span>
                    </div>
                  </div>
                ))}
                <div className="pt-2 border-t">
                  <div className="flex items-center justify-between font-semibold">
                    <span>Overall Score:</span>
                    <span className="text-lg">{response_a?.overall_score?.toFixed(3) || 'N/A'}</span>
                  </div>
                </div>
              </div>
            </div>

            <div>
              <h4 className="font-semibold mb-3">Configuration B Scores</h4>
              <div className="space-y-2">
                {dimensions.map((dim) => (
                  <div key={dim} className="flex items-center justify-between">
                    <span className="text-sm">{dimensionLabels[dim]}:</span>
                    <div className="flex items-center gap-2">
                      <div className="w-32 bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-green-600 h-2 rounded-full"
                          style={{ width: `${(response_b?.scores?.[dim] || 0) * 100}%` }}
                        />
                      </div>
                      <span className="text-sm font-medium w-12 text-right">
                        {(response_b?.scores?.[dim] || 0).toFixed(2)}
                      </span>
                    </div>
                  </div>
                ))}
                <div className="pt-2 border-t">
                  <div className="flex items-center justify-between font-semibold">
                    <span>Overall Score:</span>
                    <span className="text-lg">{response_b?.overall_score?.toFixed(3) || 'N/A'}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Explanation */}
          {explanation && (
            <div className="pt-4 border-t">
              <h4 className="font-semibold mb-2">Explanation</h4>
              <p className="text-sm text-muted-foreground">{explanation}</p>
            </div>
          )}

          {/* Strengths/Weaknesses */}
          {(response_a?.strengths?.length || response_a?.weaknesses?.length) && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4 border-t">
              <div>
                <h4 className="font-semibold mb-2">Configuration A</h4>
                {response_a.strengths?.length > 0 && (
                  <div className="mb-2">
                    <span className="text-xs font-medium text-green-700">Strengths:</span>
                    <ul className="text-xs text-muted-foreground list-disc list-inside">
                      {response_a.strengths.map((s: string, i: number) => (
                        <li key={i}>{s}</li>
                      ))}
                    </ul>
                  </div>
                )}
                {response_a.weaknesses?.length > 0 && (
                  <div>
                    <span className="text-xs font-medium text-red-700">Weaknesses:</span>
                    <ul className="text-xs text-muted-foreground list-disc list-inside">
                      {response_a.weaknesses.map((w: string, i: number) => (
                        <li key={i}>{w}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>

              <div>
                <h4 className="font-semibold mb-2">Configuration B</h4>
                {response_b.strengths?.length > 0 && (
                  <div className="mb-2">
                    <span className="text-xs font-medium text-green-700">Strengths:</span>
                    <ul className="text-xs text-muted-foreground list-disc list-inside">
                      {response_b.strengths.map((s: string, i: number) => (
                        <li key={i}>{s}</li>
                      ))}
                    </ul>
                  </div>
                )}
                {response_b.weaknesses?.length > 0 && (
                  <div>
                    <span className="text-xs font-medium text-red-700">Weaknesses:</span>
                    <ul className="text-xs text-muted-foreground list-disc list-inside">
                      {response_b.weaknesses.map((w: string, i: number) => (
                        <li key={i}>{w}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

