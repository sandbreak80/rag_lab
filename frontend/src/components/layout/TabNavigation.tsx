import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { cn } from '../../utils/formatting';
import {
  MessageSquare,
  FolderOpen,
  Settings,
  BarChart3,
  BookOpen,
  HelpCircle,
  MessageCircle,
  FileText,
  Activity,
  RefreshCw,
  FileCode,
  GitCompare,
  Cpu,
} from 'lucide-react';

const tabs = [
  { id: 'chat', label: 'Chat', icon: MessageSquare, path: '/' },
  { id: 'documents', label: 'Documents', icon: FolderOpen, path: '/documents' },
  { id: 'research', label: 'Research Agent', icon: RefreshCw, path: '/research' },
  { id: 'prompts', label: 'Prompts', icon: FileCode, path: '/prompts' },
  { id: 'ab-testing', label: 'A/B Testing', icon: GitCompare, path: '/ab-testing' },
  { id: 'gpu', label: 'GPU Monitor', icon: Cpu, path: '/gpu' },
  { id: 'settings', label: 'Settings', icon: Settings, path: '/settings' },
  { id: 'metrics', label: 'Metrics', icon: BarChart3, path: '/metrics' },
  { id: 'monitoring', label: 'Monitoring', icon: Activity, path: '/monitoring' },
  { id: 'logging', label: 'Prompt Logs', icon: FileText, path: '/logging' },
  { id: 'lab', label: 'Lab Guide', icon: BookOpen, path: '/lab' },
  { id: 'learning', label: 'Learning Hub', icon: HelpCircle, path: '/learning' },
  { id: 'feedback', label: 'Feedback', icon: MessageCircle, path: '/feedback' },
];

export function TabNavigation() {
  const location = useLocation();

  return (
    <nav className="border-b bg-card">
      <div className="container mx-auto px-6">
        <div className="flex space-x-1">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = location.pathname === tab.path;

            return (
              <Link
                key={tab.id}
                to={tab.path}
                className={cn(
                  'flex items-center gap-2 px-4 py-3 text-sm font-medium transition-colors',
                  'border-b-2 -mb-px',
                  isActive
                    ? 'border-primary text-foreground'
                    : 'border-transparent text-muted-foreground hover:text-foreground hover:border-border'
                )}
              >
                <Icon className="h-4 w-4" />
                {tab.label}
              </Link>
            );
          })}
        </div>
      </div>
    </nav>
  );
}

