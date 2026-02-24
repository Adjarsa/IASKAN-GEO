import { useState, useEffect } from 'react';

/**
 * Hook to get a stable portal container for Radix UI components
 * Fixes React 19 + Radix UI "insertBefore" error by ensuring
 * portal content is rendered into a dedicated, stable container
 */
export function usePortalContainer() {
  const [container, setContainer] = useState(() => {
    if (typeof document === 'undefined') return null;
    return document.getElementById('radix-portal-root');
  });

  useEffect(() => {
    if (container) return;
    
    // Fallback: create container if it doesn't exist
    let portalRoot = document.getElementById('radix-portal-root');
    if (!portalRoot) {
      portalRoot = document.createElement('div');
      portalRoot.id = 'radix-portal-root';
      portalRoot.setAttribute('data-radix-portal', '');
      document.body.appendChild(portalRoot);
    }
    setContainer(portalRoot);
  }, [container]);

  return container;
}

/**
 * Get portal container synchronously
 */
export function getPortalContainer() {
  if (typeof document === 'undefined') return null;
  return document.getElementById('radix-portal-root');
}
