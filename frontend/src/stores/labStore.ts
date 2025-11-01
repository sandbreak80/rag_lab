import { create } from 'zustand';
import { saveToLocalStorage, loadFromLocalStorage } from '../utils/localStorage';

interface LabExercise {
  id: string;
  title: string;
  completed: boolean;
}

interface LabStore {
  exercises: LabExercise[];
  progress: { [key: string]: boolean };
  
  // Actions
  markExerciseComplete: (exerciseId: string) => void;
  markExerciseIncomplete: (exerciseId: string) => void;
  getProgress: () => { completed: number; total: number; percentage: number };
  reset: () => void;
}

const DEFAULT_EXERCISES: LabExercise[] = [
  { id: 'ex1_baseline', title: 'Baseline Query (No Features)', completed: false },
  { id: 'ex2_vector_search', title: 'Enable Vector Search', completed: false },
  { id: 'ex3_bm25', title: 'Add BM25 Keyword Search', completed: false },
  { id: 'ex4_hybrid', title: 'Enable Hybrid Search', completed: false },
  { id: 'ex5_query_expansion', title: 'Add Query Expansion', completed: false },
  { id: 'ex6_reranking', title: 'Enable LLM Reranking', completed: false },
  { id: 'ex7_knowledge_graph', title: 'Integrate Knowledge Graph', completed: false },
  { id: 'ex8_web_search', title: 'Add Web Search', completed: false },
  { id: 'ex9_metadata_filters', title: 'Use Metadata Filters', completed: false },
  { id: 'ex10_model_comparison', title: 'Compare Different Models', completed: false },
  { id: 'ex11_temperature', title: 'Experiment with Temperature', completed: false },
  { id: 'ex12_production', title: 'Test Production Preset', completed: false },
];

export const useLabStore = create<LabStore>((set, get) => {
  const savedProgress = loadFromLocalStorage<{ [key: string]: boolean }>('lab_progress', {});

  return {
    exercises: DEFAULT_EXERCISES.map((ex) => ({
      ...ex,
      completed: savedProgress[ex.id] || false,
    })),
    progress: savedProgress,

    markExerciseComplete: (exerciseId) => {
      const progress = { ...get().progress, [exerciseId]: true };
      const exercises = get().exercises.map((ex) =>
        ex.id === exerciseId ? { ...ex, completed: true } : ex
      );
      
      set({ progress, exercises });
      saveToLocalStorage('lab_progress', progress);
    },

    markExerciseIncomplete: (exerciseId) => {
      const progress = { ...get().progress, [exerciseId]: false };
      const exercises = get().exercises.map((ex) =>
        ex.id === exerciseId ? { ...ex, completed: false } : ex
      );
      
      set({ progress, exercises });
      saveToLocalStorage('lab_progress', progress);
    },

    getProgress: () => {
      const exercises = get().exercises;
      const completed = exercises.filter((ex) => ex.completed).length;
      const total = exercises.length;
      const percentage = total > 0 ? (completed / total) * 100 : 0;

      return { completed, total, percentage };
    },

    reset: () => {
      const exercises = DEFAULT_EXERCISES;
      set({ exercises, progress: {} });
      saveToLocalStorage('lab_progress', {});
    },
  };
});

