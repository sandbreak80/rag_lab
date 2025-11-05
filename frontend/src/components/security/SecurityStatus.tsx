import React from 'react';
import { Shield, AlertTriangle, Check, X } from 'lucide-react';

interface SecurityViolation {
  type: string;
  severity: string;
  details: string;
}

interface SecurityStatusProps {
  violations?: SecurityViolation[];
  cleanedQueryUsed?: boolean;
  enabled?: boolean;
}

export const SecurityStatus: React.FC<SecurityStatusProps> = ({
  violations = [],
  cleanedQueryUsed = false,
  enabled = true,
}) => {
  if (!enabled) {
    return null;
  }

  const hasViolations = violations.length > 0;
  const criticalViolations = violations.filter((v) => v.severity === 'critical');
  const highViolations = violations.filter((v) => v.severity === 'high');
  const mediumViolations = violations.filter((v) => v.severity === 'medium');

  return (
    <div className="space-y-2">
      {/* Security Status Indicator */}
      <div
        className={`flex items-center gap-2 p-3 rounded-lg border ${
          hasViolations
            ? 'bg-yellow-50 border-yellow-200 dark:bg-yellow-900/20 dark:border-yellow-800'
            : 'bg-green-50 border-green-200 dark:bg-green-900/20 dark:border-green-800'
        }`}
      >
        <Shield
          className={`w-5 h-5 ${
            hasViolations ? 'text-yellow-600 dark:text-yellow-400' : 'text-green-600 dark:text-green-400'
          }`}
        />
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <span className="font-medium text-sm">
              {hasViolations ? 'Security Alert' : 'Query Secure'}
            </span>
            {!hasViolations && <Check className="w-4 h-4 text-green-600 dark:text-green-400" />}
          </div>
          <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
            {hasViolations
              ? `${violations.length} security ${violations.length === 1 ? 'issue' : 'issues'} detected and handled`
              : 'No security issues detected'}
          </p>
        </div>
      </div>

      {/* Violations Details */}
      {hasViolations && (
        <div className="space-y-2">
          {/* Critical Violations */}
          {criticalViolations.map((violation, idx) => (
            <div
              key={`critical-${idx}`}
              className="flex items-start gap-2 p-3 rounded-lg bg-red-50 border border-red-200 dark:bg-red-900/20 dark:border-red-800"
            >
              <X className="w-5 h-5 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
              <div className="flex-1 min-w-0">
                <div className="font-medium text-sm text-red-900 dark:text-red-100">
                  {violation.type === 'injection' && 'Prompt Injection Blocked'}
                  {violation.type === 'pii' && 'PII Detected'}
                  {violation.type === 'topic_violation' && 'Topic Violation'}
                  {violation.type === 'unicode_attack' && 'Unicode Attack Detected'}
                </div>
                <p className="text-xs text-red-700 dark:text-red-300 mt-1">
                  {violation.details}
                </p>
              </div>
            </div>
          ))}

          {/* High Violations */}
          {highViolations.map((violation, idx) => (
            <div
              key={`high-${idx}`}
              className="flex items-start gap-2 p-3 rounded-lg bg-orange-50 border border-orange-200 dark:bg-orange-900/20 dark:border-orange-800"
            >
              <AlertTriangle className="w-5 h-5 text-orange-600 dark:text-orange-400 flex-shrink-0 mt-0.5" />
              <div className="flex-1 min-w-0">
                <div className="font-medium text-sm text-orange-900 dark:text-orange-100">
                  {violation.type === 'pii' && 'PII Redacted'}
                  {violation.type === 'unicode_attack' && 'Suspicious Characters Removed'}
                </div>
                <p className="text-xs text-orange-700 dark:text-orange-300 mt-1">
                  {violation.details}
                </p>
              </div>
            </div>
          ))}

          {/* Medium Violations */}
          {mediumViolations.map((violation, idx) => (
            <div
              key={`medium-${idx}`}
              className="flex items-start gap-2 p-3 rounded-lg bg-yellow-50 border border-yellow-200 dark:bg-yellow-900/20 dark:border-yellow-800"
            >
              <AlertTriangle className="w-5 h-5 text-yellow-600 dark:text-yellow-400 flex-shrink-0 mt-0.5" />
              <div className="flex-1 min-w-0">
                <div className="font-medium text-sm text-yellow-900 dark:text-yellow-100">
                  {violation.type === 'topic_violation' && 'Topic Warning'}
                  {violation.type === 'security_service_error' && 'Security Service Warning'}
                </div>
                <p className="text-xs text-yellow-700 dark:text-yellow-300 mt-1">
                  {violation.details}
                </p>
              </div>
            </div>
          ))}

          {/* Query Cleaned Notice */}
          {cleanedQueryUsed && (
            <div className="flex items-start gap-2 p-3 rounded-lg bg-blue-50 border border-blue-200 dark:bg-blue-900/20 dark:border-blue-800">
              <Shield className="w-5 h-5 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5" />
              <div className="flex-1 min-w-0">
                <div className="font-medium text-sm text-blue-900 dark:text-blue-100">
                  Query Sanitized
                </div>
                <p className="text-xs text-blue-700 dark:text-blue-300 mt-1">
                  Your query was automatically cleaned for security purposes
                </p>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default SecurityStatus;

