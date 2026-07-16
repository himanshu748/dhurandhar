import { Flip } from "gsap/Flip";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { REDUCED_MOTION_QUERY } from "./motion";

gsap.registerPlugin(ScrollTrigger, Flip);

export { Flip, gsap, REDUCED_MOTION_QUERY, ScrollTrigger };
