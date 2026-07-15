import {
  BookOpen,
  Bot,
  Braces,
  ClipboardCheck,
  CloudCog,
  Monitor,
  Radar,
  ScrollText,
  ShieldCheck,
} from "lucide-react";

const roleIcon = (role: string) => {
  const normalized = role.toLowerCase();
  if (normalized.includes("product") || normalized.includes("atlas")) return { Icon: ScrollText, token: "product" };
  if (normalized.includes("frontend") || normalized.includes("prism")) return { Icon: Monitor, token: "frontend" };
  if (normalized.includes("backend") || normalized.includes("forge")) return { Icon: Braces, token: "backend" };
  if (normalized.includes("platform") || normalized.includes("rivet")) return { Icon: CloudCog, token: "platform" };
  if (normalized.includes("review") || normalized.includes("aegis")) return { Icon: ShieldCheck, token: "reviewer" };
  if (normalized.includes("qa") || normalized.includes("saboteur") || normalized.includes("sentinel")) return { Icon: ClipboardCheck, token: "qa" };
  if (normalized.includes("release") || normalized.includes("recovery") || normalized.includes("shipwright")) return { Icon: Radar, token: "release" };
  if (normalized.includes("histor") || normalized.includes("chronicle")) return { Icon: BookOpen, token: "historian" };
  return { Icon: Bot, token: "agent" };
};

export function RoleMark({ role, showLabel = true }: { role: string; showLabel?: boolean }) {
  const { Icon, token } = roleIcon(role);
  return (
    <span className={`role-mark role-${token}`}>
      <Icon size={16} strokeWidth={2} aria-hidden="true" />
      {showLabel && <span>{role}</span>}
    </span>
  );
}
