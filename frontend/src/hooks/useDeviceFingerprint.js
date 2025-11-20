import { useState, useEffect } from 'react';
import { getDeviceFingerprint } from '../utils/deviceFingerprint';

export const useDeviceFingerprint = () => {
  const [fingerprint, setFingerprint] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchFingerprint = async () => {
      try {
        const fp = await getDeviceFingerprint();
        setFingerprint(fp);
      } catch (error) {
        console.error('Failed to get device fingerprint:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchFingerprint();
  }, []);

  return { fingerprint, loading };
};
