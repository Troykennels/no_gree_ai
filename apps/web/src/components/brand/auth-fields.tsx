"use client";

import { useState } from "react";
import { Eye, EyeOff, Lock } from "lucide-react";

/** Icon-prefixed text input used on the auth screens (mockup .field/.box). */
export function Field({
  id,
  label,
  icon,
  value,
  onChange,
  ...rest
}: {
  id: string;
  label: string;
  icon: React.ReactNode;
  value: string;
  onChange: (v: string) => void;
} & Omit<React.InputHTMLAttributes<HTMLInputElement>, "value" | "onChange">) {
  return (
    <div className="field">
      <label htmlFor={id}>{label}</label>
      <div className="box">
        {icon}
        <input
          id={id}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          {...rest}
        />
      </div>
    </div>
  );
}

/** Password input with a show/hide toggle. */
export function PasswordField({
  value,
  onChange,
  autoComplete,
  minLength,
  label = "Password",
  placeholder = "••••••••",
}: {
  value: string;
  onChange: (v: string) => void;
  autoComplete: string;
  minLength?: number;
  label?: string;
  placeholder?: string;
}) {
  const [show, setShow] = useState(false);
  return (
    <div className="field">
      <label htmlFor="password">{label}</label>
      <div className="box">
        <Lock />
        <input
          id="password"
          type={show ? "text" : "password"}
          autoComplete={autoComplete}
          required
          minLength={minLength}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
        />
        <button
          type="button"
          className="eye"
          onClick={() => setShow((v) => !v)}
          aria-label={show ? "Hide password" : "Show password"}
          style={{ display: "grid", placeItems: "center", background: "none", border: 0, color: "var(--muted-hex)" }}
        >
          {show ? <EyeOff /> : <Eye />}
        </button>
      </div>
    </div>
  );
}
