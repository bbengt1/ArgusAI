/**
 * Skip to Content Link Component (Story P6-2.1)
 *
 * Accessibility feature that allows keyboard users to bypass navigation
 * and jump directly to main content. WCAG 2.4.1 Bypass Blocks compliance.
 *
 * - Visually hidden by default using sr-only
 * - Becomes visible and styled when focused
 * - Links to #main-content anchor on the main element
 */

'use client';

export function SkipToContent() {
  return (
    <a
      href="#main-content"
      className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-[100] focus:px-4 focus:py-2 focus:bg-primary focus:text-primary-foreground focus:rounded-md focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 focus:ring-offset-background"
    >
      Skip to content
    </a>
  );
}
