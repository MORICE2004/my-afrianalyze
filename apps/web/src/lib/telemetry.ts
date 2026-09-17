/**
 * Frontend telemetry wrapper for Sentry and PostHog.
 * Designed to scrub sensitive data before sending and allows total disablement via env vars.
 */

const POSTHOG_ENABLED = process.env.NEXT_PUBLIC_POSTHOG_ENABLED === "true";
const SENTRY_ENABLED = process.env.NEXT_PUBLIC_SENTRY_ENABLED === "true";

function scrubData(data: Record<string, any>): Record<string, any> {
    const sensitiveKeys = ["password", "api_key", "secret", "financial_data", "source_doc"];
    const scrubbed: Record<string, any> = {};

    for (const [key, value] of Object.entries(data)) {
        if (sensitiveKeys.some(s => key.toLowerCase().includes(s))) {
            scrubbed[key] = "[SCRUBBED]";
        } else if (value && typeof value === "object" && !Array.isArray(value)) {
            scrubbed[key] = scrubData(value);
        } else {
            scrubbed[key] = value;
        }
    }
    return scrubbed;
}

export const captureEvent = (eventName: string, properties?: Record<string, any>) => {
    if (!POSTHOG_ENABLED) return;
    
    const safeProps = properties ? scrubData(properties) : {};
    console.log(`[PostHog] Captured Event: ${eventName}`, safeProps);
    // window.posthog.capture(eventName, safeProps)
};

export const captureException = (error: Error, context?: Record<string, any>) => {
    if (!SENTRY_ENABLED) return;
    
    const safeContext = context ? scrubData(context) : {};
    console.error(`[Sentry] Captured Exception:`, error, safeContext);
    // Sentry.captureException(error, { extra: safeContext })
};
