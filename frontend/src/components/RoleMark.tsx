import {
  Bot,
  Braces,
  ClipboardCheck,
  CloudCog,
  Radar,
  ScrollText,
  ShieldCheck,
} from "lucide-react";

const roleIcon = (role: string) => {
  const normalized = role.toLowerCase();
  if (normalized.includes("engineer")) return Braces;
  if (normalized.includes("review")) return ShieldCheck;
  if (normalized.includes("qa")) return ClipboardCheck;
  if (normalized.includes("deploy")) return CloudCog;
  if (normalized.includes("monitor")) return Radar;
  if (normalized.includes("policy")) return ScrollText;
  return Bot;
};

export function RoleMark({ role, showLabel = true }: { role: string; showLabel?: boolean }) {
  const Icon = roleIcon(role);
  const token = role.toLowerCase().replace(/\s+agent|\s+/g, "-");
  return (
    <span className={`role-mark role-${token}`}>
      <Icon size={16} strokeWidth={2} aria-hidden="true" />
      {showLabel && <span>{role}</span>}
    </span>
  );
}
