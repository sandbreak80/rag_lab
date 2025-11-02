import * as React from 'react';
import { cn } from '../../utils/formatting';

export interface SwitchProps extends React.InputHTMLAttributes<HTMLInputElement> {
  checked?: boolean;
  onCheckedChange?: (checked: boolean) => void;
}

const Switch = React.forwardRef<HTMLInputElement, SwitchProps>(
  ({ className, checked, onCheckedChange, ...props }, ref) => {
    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
      onCheckedChange?.(e.target.checked);
    };

    return (
      <label className={cn("relative inline-flex cursor-pointer items-center", className)}>
        <input
          type="checkbox"
          className="sr-only"
          checked={checked}
          onChange={handleChange}
          ref={ref}
          {...props}
        />
        <div
          className={cn(
            'relative w-11 h-6 rounded-full transition-colors duration-200',
            checked ? 'bg-primary' : 'bg-muted'
          )}
        >
          <div
            className={cn(
              'absolute top-0.5 left-0.5 bg-background rounded-full h-5 w-5',
              'transition-transform duration-200 ease-in-out',
              'shadow-sm',
              checked ? 'translate-x-5' : 'translate-x-0'
            )}
          />
        </div>
      </label>
    );
  }
);

Switch.displayName = 'Switch';

export { Switch };

