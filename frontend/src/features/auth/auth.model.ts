export type User = {
  id: number;
  company_id: number;
  full_name: string;
  email: string;
};

export type LoginForm = { email: string; password: string };

export type SignupForm = LoginForm & { company_name: string; full_name: string };
