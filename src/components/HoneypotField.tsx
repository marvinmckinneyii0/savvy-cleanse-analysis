import React from 'react';

interface HoneypotFieldProps {
  value: string;
  onChange: (value: string) => void;
}

/**
 * Spam trap: invisible to people and skipped by keyboard and screen readers.
 * Bots that fill every input reveal themselves by filling this one.
 */
const HoneypotField = ({ value, onChange }: HoneypotFieldProps) => (
  <div aria-hidden="true" className="absolute -left-[9999px] h-0 w-0 overflow-hidden">
    <label>
      Leave this field empty
      <input
        type="text"
        name="_gotcha"
        tabIndex={-1}
        autoComplete="off"
        value={value}
        onChange={(e) => onChange(e.target.value)}
      />
    </label>
  </div>
);

export default HoneypotField;
