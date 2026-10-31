import type { Candidate } from "../candidates.model";

export function Avatar({ candidate, large }: { candidate: Candidate; large?: boolean }) {
  const initials = candidate.full_name_en.split(" ").map((word) => word[0]).join("").slice(0, 2).toUpperCase();
  return (
    <span className={large ? "avatar avatar-large" : "avatar"}>
      {candidate.avatar_url ? <img src={candidate.avatar_url} alt="" /> : initials}
    </span>
  );
}
