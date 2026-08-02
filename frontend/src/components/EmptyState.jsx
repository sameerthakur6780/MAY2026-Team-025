export default function EmptyState({ icon: Icon, title, description, action }) {
  return (
    <div className="flex flex-col items-center justify-center text-center py-14 px-6">
      {Icon && (
        <div className="w-12 h-12 rounded-xl bg-sage/60 flex items-center justify-center mb-4">
          <Icon className="w-6 h-6 text-forest" />
        </div>
      )}
      <div className="font-display text-lg font-semibold text-forest">{title}</div>
      {description && <p className="text-sm text-[#5C5C5C] mt-1.5 max-w-sm">{description}</p>}
      {action && <div className="mt-5">{action}</div>}
    </div>
  );
}
