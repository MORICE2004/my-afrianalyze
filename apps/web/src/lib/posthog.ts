export const posthog = {
  capture: (eventName: string, properties?: Record<string, any>) => {
    console.log(`[PostHog Mock] Captured event: ${eventName}`, properties);
  },
  identify: (distinctId: string, properties?: Record<string, any>) => {
    console.log(`[PostHog Mock] Identified user: ${distinctId}`, properties);
  },
};
