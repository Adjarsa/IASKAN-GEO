import { useState, useEffect, useCallback } from 'react';

/**
 * Hook to get a stable portal container for Radix UI components
 * Fixes React 19 + Radix UI "insertBefore" error by ensuring
 * portal content is rendered into a dedicated, stable container
 */
export function usePortalContainer() {
  const [container, setContainer] = useState(null);

  useEffect(() => {
    // Wait for DOM to be fully ready
    const getOrCreateContainer = () => {
      let portalRoot = document.getElementById('radix-portal-root');
      if (!portalRoot) {
        portalRoot = document.createElement('div');
        portalRoot.id = 'radix-portal-root';
        portalRoot.setAttribute('data-radix-portal', '');
        document.body.appendChild(portalRoot);
      }
      return portalRoot;
    };

    // Use requestAnimationFrame to ensure DOM is ready
    const rafId = requestAnimationFrame(() => {
      setContainer(getOrCreateContainer());
    });

    return () => cancelAnimationFrame(rafId);
  }, []);

  return container;
}

/**
 * Creates a portal container element synchronously
 * Use this for SSR or when you need the container immediately
 */
export function getPortalContainer() {
  if (typeof document === 'undefined') return null;
  
  let portalRoot = document.getElementById('radix-portal-root');
  if (!portalRoot) {
    portalRoot = document.createElement('div');
    portalRoot.id = 'radix-portal-root';
    portalRoot.setAttribute('data-radix-portal', '');
    document.body.appendChild(portalRoot);
  }
  return portalRoot;
}
