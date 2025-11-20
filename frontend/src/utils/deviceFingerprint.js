import FingerprintJS from '@fingerprintjs/fingerprintjs';

let fpPromise = null;

export const getDeviceFingerprint = async () => {
  try {
    // Initialize FingerprintJS if not already done
    if (!fpPromise) {
      fpPromise = FingerprintJS.load();
    }

    const fp = await fpPromise;
    const result = await fp.get();

    // Return the visitor ID as device fingerprint
    return result.visitorId;
  } catch (error) {
    console.error('Failed to get device fingerprint:', error);
    // Return a fallback fingerprint
    return `fallback-${Date.now()}-${Math.random()}`;
  }
};

export const getBrowserInfo = () => {
  const userAgent = navigator.userAgent;
  let browserName = 'Unknown';
  let osName = 'Unknown';

  // Detect browser
  if (userAgent.indexOf('Firefox') > -1) {
    browserName = 'Firefox';
  } else if (userAgent.indexOf('Chrome') > -1) {
    browserName = 'Chrome';
  } else if (userAgent.indexOf('Safari') > -1) {
    browserName = 'Safari';
  } else if (userAgent.indexOf('Edge') > -1) {
    browserName = 'Edge';
  }

  // Detect OS
  if (userAgent.indexOf('Win') > -1) {
    osName = 'Windows';
  } else if (userAgent.indexOf('Mac') > -1) {
    osName = 'MacOS';
  } else if (userAgent.indexOf('Linux') > -1) {
    osName = 'Linux';
  } else if (userAgent.indexOf('Android') > -1) {
    osName = 'Android';
  } else if (userAgent.indexOf('iOS') > -1) {
    osName = 'iOS';
  }

  return { browserName, osName };
};
