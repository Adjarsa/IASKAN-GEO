/**
 * Browser Fingerprint Hook
 * Uses FingerprintJS to generate a unique browser identifier
 * Used for anti-abuse protection on free trial
 */

import { useState, useEffect } from 'react';
import FingerprintJS from '@fingerprintjs/fingerprintjs';

// Singleton to store fingerprint
let cachedFingerprint = null;
let fingerprintPromise = null;

/**
 * Hook to get browser fingerprint
 * Returns { fingerprint, loading, error }
 */
export const useFingerprint = () => {
  const [fingerprint, setFingerprint] = useState(cachedFingerprint);
  const [loading, setLoading] = useState(!cachedFingerprint);
  const [error, setError] = useState(null);

  useEffect(() => {
    const loadFingerprint = async () => {
      // Return cached value if available
      if (cachedFingerprint) {
        setFingerprint(cachedFingerprint);
        setLoading(false);
        return;
      }

      // Reuse existing promise if loading
      if (fingerprintPromise) {
        try {
          const result = await fingerprintPromise;
          setFingerprint(result);
          setLoading(false);
        } catch (err) {
          setError(err);
          setLoading(false);
        }
        return;
      }

      // Create new fingerprint
      fingerprintPromise = (async () => {
        try {
          const fp = await FingerprintJS.load();
          const result = await fp.get();
          cachedFingerprint = result.visitorId;
          return cachedFingerprint;
        } catch (err) {
          console.error('Fingerprint error:', err);
          // Return a fallback fingerprint based on available data
          const fallback = generateFallbackFingerprint();
          cachedFingerprint = fallback;
          return fallback;
        }
      })();

      try {
        const result = await fingerprintPromise;
        setFingerprint(result);
        setLoading(false);
      } catch (err) {
        setError(err);
        setLoading(false);
      }
    };

    loadFingerprint();
  }, []);

  return { fingerprint, loading, error };
};

/**
 * Generate a fallback fingerprint if FingerprintJS fails
 */
const generateFallbackFingerprint = () => {
  const components = [
    navigator.userAgent,
    navigator.language,
    screen.width,
    screen.height,
    screen.colorDepth,
    new Date().getTimezoneOffset(),
    navigator.hardwareConcurrency || 'unknown',
    navigator.platform || 'unknown'
  ];
  
  // Simple hash function
  const hash = components.join('|');
  let hashCode = 0;
  for (let i = 0; i < hash.length; i++) {
    const char = hash.charCodeAt(i);
    hashCode = ((hashCode << 5) - hashCode) + char;
    hashCode = hashCode & hashCode; // Convert to 32-bit integer
  }
  
  return `fallback_${Math.abs(hashCode).toString(16)}`;
};

/**
 * Get fingerprint synchronously (returns cached value or null)
 */
export const getFingerprint = () => cachedFingerprint;

/**
 * Get fingerprint asynchronously (waits for it to be ready)
 */
export const getFingerprintAsync = async () => {
  if (cachedFingerprint) return cachedFingerprint;
  
  if (fingerprintPromise) {
    return await fingerprintPromise;
  }
  
  // Initialize if not started
  try {
    const fp = await FingerprintJS.load();
    const result = await fp.get();
    cachedFingerprint = result.visitorId;
    return cachedFingerprint;
  } catch (err) {
    const fallback = generateFallbackFingerprint();
    cachedFingerprint = fallback;
    return fallback;
  }
};

export default useFingerprint;
