import { useLayoutEffect, useRef } from "react";
import { useReducedMotion } from "../hooks/useReducedMotion";
import { gsap } from "../lib/gsap";

export function AnimatedNumber({
  value,
  className,
  prefix = "",
  suffix = "",
  decimals = 0,
  duration = 0.55,
}: {
  value: number;
  className?: string;
  prefix?: string;
  suffix?: string;
  decimals?: number;
  duration?: number;
}) {
  const element = useRef<HTMLElement | null>(null);
  const previous = useRef(value);
  const reducedMotion = useReducedMotion();
  const format = (number: number) => `${prefix}${number.toLocaleString("en-US", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  })}${suffix}`;

  useLayoutEffect(() => {
    const node = element.current;
    if (!node) return undefined;
    const counter = { value: previous.current };
    const context = gsap.context(() => {
      if (reducedMotion) {
        node.textContent = format(value);
        return;
      }
      gsap.to(counter, {
        value,
        duration,
        ease: "power2.out",
        overwrite: true,
        onUpdate: () => {
          node.textContent = format(counter.value);
        },
      });
    }, node);
    previous.current = value;
    return () => context.revert();
  }, [decimals, duration, prefix, reducedMotion, suffix, value]);

  return <code ref={element} className={className}>{format(value)}</code>;
}
