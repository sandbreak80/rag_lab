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
      <label className="relative inline-flex cursor-pointer items-center">
        <input
          type="checkbox"
          className="sr-only peer"
          checked={checked}
          onChange={handleChange}
          ref={ref}
          {...props}
        />
        <div
          className={cn(
            'w-11 h-6 bg-muted rounded-full peer',
            'peer-checked:bg-primary',
            'peer-focus:ring-2 peer-focus:ring-ring peer-focus:ring-offset-2 peer-focus:ring-offset-background',
            'transition-colors',
            className
          )}
        >
          <div
            className={cn(
              'absolute top-0.5 left-0.5 bg-background rounded-full h-5 w-5',
              'transition-transform peer-checked:translate-x-5',
              'shadow-sm'
            )}
          />
        </div>
      </label>
    );
  }
);

Switch.displayName = 'Switch';

export { Switch };

