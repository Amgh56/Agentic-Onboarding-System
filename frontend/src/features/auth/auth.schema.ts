import type { MessageKey } from "@/shared/lib/i18n";
import type { LoginForm, SignupForm } from "./auth.model";

export type FormErrors<T> = Partial<Record<keyof T, MessageKey>>;

export function validateLogin(values: LoginForm): FormErrors<LoginForm> {
  const errors: FormErrors<LoginForm> = {};
  if (!values.email.trim()) errors.email = "error.required";
  if (!values.password) errors.password = "error.required";
  return errors;
}

export function validateSignup(values: SignupForm): FormErrors<SignupForm> {
  const errors: FormErrors<SignupForm> = {};
  if (!values.company_name.trim()) errors.company_name = "error.required";
  if (!values.full_name.trim()) errors.full_name = "error.required";
  if (!values.email.trim()) errors.email = "error.required";
  if (values.password.length < 6) errors.password = "error.password";
  return errors;
}
