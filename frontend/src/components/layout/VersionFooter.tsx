import { useQuery } from '@tanstack/react-query';
import { api } from '../../services/api';
import packageJson from '../../../package.json';

export function VersionFooter() {
  const { data: versions } = useQuery({
    queryKey: ['versions'],
    queryFn: () => api.getVersions(),
    refetchInterval: 60000, // Refresh every minute
    retry: false,
  });

  return (
    <div className="fixed bottom-0 right-0 p-2 text-xs text-muted-foreground bg-background/80 backdrop-blur-sm border-t border-l rounded-tl-lg">
      <div className="flex items-center gap-2">
        <span className="font-mono">
          UI: v{packageJson.version}
        </span>
        {versions?.gateway?.version && (
          <>
            <span>•</span>
            <span className="font-mono">
              API: v{versions.gateway.version}
            </span>
          </>
        )}
        <button
          onClick={() => window.open('/api/version', '_blank')}
          className="ml-1 px-1 hover:text-foreground transition-colors"
          title="View all service versions"
        >
          ⓘ
        </button>
      </div>
    </div>
  );
}

