import { useEffect, useState } from "react";
import { REDUCED_MOTION_QUERY } from "../lib/gsap";

const preference = () => typeof window !== "undefined"
  && typeof window.matchMedia === "function"
  && window.matchMedia(REDUCED_MOTION_QUERY).matches;

export function useReducedMotion() {
  const [reduced, setReduced] = useState(preference);

  useEffect(() => {
    if (typeof window.matchMedia !== "function") return undefined;
    const media = window.matchMedia(REDUCED_MOTION_QUERY);
    const update = () => setReduced(media.matches);
    update();
    media.addEventListener("change", update);
    return () => media.removeEventListener("change", update);
  }, []);

  return reduced;
}
