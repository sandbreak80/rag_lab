import React from 'react';
import { useLabStore } from '../../stores/labStore';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { CheckCircle, Circle } from 'lucide-react';

export function ProgressTracker() {
  const exercises = useLabStore((state) => state.exercises);
  const progress = useLabStore((state) => state.getProgress());
  const markComplete = useLabStore((state) => state.markExerciseComplete);
  const markIncomplete = useLabStore((state) => state.markExerciseIncomplete);

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">Lab Progress</CardTitle>
          <div className="text-sm text-muted-foreground">
            {progress.completed} / {progress.total} ({Math.round(progress.percentage)}%)
          </div>
        </div>
        {/* Progress bar */}
        <div className="h-2 bg-muted rounded-full overflow-hidden mt-2">
          <div
            className="h-full bg-primary transition-all duration-300"
            style={{ width: `${progress.percentage}%` }}
          />
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {exercises.map((exercise) => (
            <button
              key={exercise.id}
              onClick={() =>
                exercise.completed
                  ? markIncomplete(exercise.id)
                  : markComplete(exercise.id)
              }
              className="w-full flex items-center gap-3 p-3 rounded-lg hover:bg-muted/50 transition-colors text-left"
            >
              {exercise.completed ? (
                <CheckCircle className="h-5 w-5 text-primary flex-shrink-0" />
              ) : (
                <Circle className="h-5 w-5 text-muted-foreground flex-shrink-0" />
              )}
              <span
                className={`text-sm ${
                  exercise.completed ? 'line-through text-muted-foreground' : ''
                }`}
              >
                {exercise.title}
              </span>
            </button>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

