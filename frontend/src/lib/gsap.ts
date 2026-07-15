import { Flip } from "gsap/Flip";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

gsap.registerPlugin(ScrollTrigger, Flip);

export const REDUCED_MOTION_QUERY = "(prefers-reduced-motion: reduce)";

export { Flip, gsap, ScrollTrigger };
