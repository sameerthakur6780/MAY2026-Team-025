import { cn } from "@/lib/utils";

export default function MultiSelect({ options, value = [], onChange, className }) {
  const toggle = (optionValue) => {
    if (value.includes(optionValue)) {
      onChange(value.filter((item) => item !== optionValue));
      return;
    }
    onChange([...value, optionValue]);
  };

  if (options.length === 0) {
    return <div className={cn("text-sm text-muted-foreground", className)}>No options available.</div>;
  }

  return (
    <div className={cn("border border-soft rounded-xl p-3 space-y-2 max-h-48 overflow-y-auto bg-canvas", className)}>
      {options.map((option) => (
        <label key={option.value} className="flex items-center gap-2 cursor-pointer text-sm">
          <input
            type="checkbox"
            checked={value.includes(option.value)}
            onChange={() => toggle(option.value)}
            className="rounded border-soft"
          />
          <span>{option.label}</span>
        </label>
      ))}
    </div>
  );
}
