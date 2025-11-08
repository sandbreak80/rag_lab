import React from 'react';
import { Shield, Clock, Filter } from 'lucide-react';

interface ProvenanceBadgesProps {
  securityStatus: 'ok' | 'degraded' | 'blocked';
  recencyPassed?: boolean;
  recencyWindow?: number;
  aclFiltered?: number;
}

export const ProvenanceBadges: React.FC<ProvenanceBadgesProps> = ({
  securityStatus,
  recencyPassed,
  recencyWindow = 48,
  aclFiltered,
}) => {
  return (
    <div className="flex flex-wrap items-center gap-2">
      {/* Security Status */}
      <div className={`flex items-center gap-1 rounded-full px-2 py-1 text-xs font-medium ${
        securityStatus === 'ok' ? 'bg-green-100 text-green-700' :
        securityStatus === 'degraded' ? 'bg-yellow-100 text-yellow-700' :
        'bg-red-100 text-red-700'
      }`}>
        <Shield className="h-3 w-3" />
        {securityStatus.toUpperCase()}
      </div>

      {/* Recency Badge */}
      {recencyPassed !== undefined && (
        <div className={`flex items-center gap-1 rounded-full px-2 py-1 text-xs font-medium ${
          recencyPassed ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-600'
        }`}>
          <Clock className="h-3 w-3" />
          {recencyPassed ? `≤${recencyWindow}h` : `>${recencyWindow}h`}
        </div>
      )}

      {/* ACL Filtered */}
      {aclFiltered !== undefined && aclFiltered > 0 && (
        <div className="flex items-center gap-1 rounded-full bg-purple-100 px-2 py-1 text-xs font-medium text-purple-700">
          <Filter className="h-3 w-3" />
          {aclFiltered} filtered
        </div>
      )}
    </div>
  );
};

