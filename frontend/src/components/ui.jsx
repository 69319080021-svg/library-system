// ชิ้นส่วนหน้าจอที่ใช้ซ้ำ

export function PageTitle({ children, action }) {
  return (
    <div className="mb-4 flex items-center justify-between gap-3">
      <h1 className="text-xl font-bold text-slate-900">{children}</h1>
      {action}
    </div>
  )
}

export function Card({ children, className = '' }) {
  return (
    <div className={`rounded-xl border border-slate-200 bg-white p-4 shadow-sm ${className}`}>
      {children}
    </div>
  )
}

const BUTTON_STYLES = {
  primary: 'bg-teal-700 text-white hover:bg-teal-800',
  secondary: 'border border-slate-300 bg-white text-slate-700 hover:bg-slate-50',
  danger: 'border border-red-200 bg-white text-red-700 hover:bg-red-50',
}

export function Button({ variant = 'primary', className = '', ...props }) {
  return (
    <button
      className={`inline-flex min-h-10 items-center justify-center rounded-lg px-4 py-2 text-sm font-semibold transition disabled:cursor-not-allowed disabled:opacity-50 ${BUTTON_STYLES[variant]} ${className}`}
      {...props}
    />
  )
}

export function Field({ label, hint, ...props }) {
  return (
    <label className="block">
      <span className="mb-1 block text-sm font-medium text-slate-700">{label}</span>
      <input
        className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-base outline-none focus:border-teal-600 focus:ring-2 focus:ring-teal-600/20"
        {...props}
      />
      {hint && <span className="mt-1 block text-xs text-slate-500">{hint}</span>}
    </label>
  )
}

export function SearchBox({ value, onChange, placeholder }) {
  return (
    <input
      type="search"
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder={placeholder}
      className="mb-3 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-base outline-none focus:border-teal-600 focus:ring-2 focus:ring-teal-600/20"
    />
  )
}

const ALERT_STYLES = {
  error: 'border-red-200 bg-red-50 text-red-800',
  success: 'border-green-200 bg-green-50 text-green-800',
}

export function Alert({ type = 'error', children, onClose }) {
  if (!children) return null
  return (
    <div
      role={type === 'error' ? 'alert' : 'status'}
      className={`mb-3 flex items-start justify-between gap-3 rounded-lg border px-3 py-2 text-sm ${ALERT_STYLES[type]}`}
    >
      <span>{children}</span>
      {onClose && (
        <button onClick={onClose} className="shrink-0 font-bold opacity-60 hover:opacity-100" aria-label="ปิด">
          ✕
        </button>
      )}
    </div>
  )
}

const BADGE_STYLES = {
  green: 'bg-green-100 text-green-800',
  amber: 'bg-amber-100 text-amber-800',
  red: 'bg-red-100 text-red-800',
  gray: 'bg-slate-100 text-slate-600',
}

export function Badge({ color = 'gray', children }) {
  return (
    <span className={`inline-block rounded-full px-2 py-0.5 text-xs font-semibold ${BADGE_STYLES[color]}`}>
      {children}
    </span>
  )
}

export function Empty({ children }) {
  return <p className="py-8 text-center text-sm text-slate-500">{children}</p>
}
