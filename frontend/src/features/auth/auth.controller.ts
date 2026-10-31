"use client";

import { useEffect, useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { clearToken, getToken } from "@/shared/lib/api-client";
import type { LoginForm, SignupForm, User } from "./auth.model";
import { validateLogin, validateSignup, type FormErrors } from "./auth.schema";
import * as authService from "./auth.service";

function useAuthForm<T extends Record<string, string>>(
  initial: T,
  validate: (values: T) => FormErrors<T>,
  submit: (values: T) => Promise<void>,
) {
  const router = useRouter();
  const [values, setValues] = useState(initial);
  const [errors, setErrors] = useState<FormErrors<T>>({});
  const [serverError, setServerError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  function onChange(field: keyof T, value: string) {
    setValues({ ...values, [field]: value });
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    const found = validate(values);
    setErrors(found);
    if (Object.keys(found).length > 0) return;

    setSubmitting(true);
    setServerError("");
    try {
      await submit(values);
      router.replace("/jobs");
    } catch (error) {
      setServerError(error instanceof Error ? error.message : "Something went wrong");
      setSubmitting(false);
    }
  }

  return { values, errors, serverError, submitting, onChange, onSubmit };
}

export const useLoginForm = () =>
  useAuthForm<LoginForm>({ email: "", password: "" }, validateLogin, authService.login);

export const useSignupForm = () =>
  useAuthForm<SignupForm>(
    { company_name: "", full_name: "", email: "", password: "" },
    validateSignup,
    authService.signup,
  );

export function useCurrentUser() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    authService.getMe().then(setUser).catch(() => {
      clearToken();
      router.replace("/login");
    });
  }, [router]);

  function logout() {
    clearToken();
    router.replace("/login");
  }

  return { user, logout };
}
