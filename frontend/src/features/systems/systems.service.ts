import { api } from "@/shared/lib/api-client";
import type { SystemContents } from "./systems.model";

export const getContents = () => api<SystemContents[]>("/systems/contents");
