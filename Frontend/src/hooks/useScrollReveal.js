import { useEffect, useRef, useState } from 'react';

/**
 * useScrollReveal – lightweight Intersection Observer hook.
 * Returns a ref to attach to the target element, plus a boolean `inView`.
 *
 * @param {object} opts
 * @param {number} opts.threshold   – 0–1 fraction of element visible (default 0.15)
 * @param {string} opts.rootMargin  – CSS root margin (default '0px 0px -60px 0px')
 * @param {boolean} opts.once       – only trigger once (default true)
 */
export function useScrollReveal({
  threshold = 0.15,
  rootMargin = '0px 0px -60px 0px',
  once = true,
} = {}) {
  const ref = useRef(null);
  const [inView, setInView] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setInView(true);
          if (once) observer.unobserve(el);
        } else if (!once) {
          setInView(false);
        }
      },
      { threshold, rootMargin }
    );

    observer.observe(el);
    return () => observer.disconnect();
  }, [threshold, rootMargin, once]);

  return { ref, inView };
}
