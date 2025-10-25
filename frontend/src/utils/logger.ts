/**
 * Centralized logging utility for frontend
 *
 * This logger:
 * - Disables console.log in production
 * - Preserves logging in development
 * - Can be extended to send errors to external services (Sentry, LogRocket, etc.)
 */

const isDevelopment = import.meta.env.DEV;

class Logger {
  /**
   * Log general information (disabled in production)
   */
  log(...args: any[]) {
    if (isDevelopment) {
      console.log(...args);
    }
  }

  /**
   * Log debugging information (disabled in production)
   */
  debug(...args: any[]) {
    if (isDevelopment) {
      console.debug(...args);
    }
  }

  /**
   * Log warnings (always enabled)
   */
  warn(...args: any[]) {
    console.warn(...args);
    // TODO: Send to error tracking service in production
    // if (!isDevelopment) {
    //   Sentry.captureMessage(args.join(' '), 'warning');
    // }
  }

  /**
   * Log errors (always enabled)
   */
  error(...args: any[]) {
    console.error(...args);
    // TODO: Send to error tracking service in production
    // if (!isDevelopment) {
    //   Sentry.captureException(args[0]);
    // }
  }

  /**
   * Log API requests (only in development)
   */
  api(method: string, url: string, data?: any) {
    if (isDevelopment) {
      console.group(`[API] ${method} ${url}`);
      if (data) {
        console.log('Data:', data);
      }
      console.groupEnd();
    }
  }

  /**
   * Log authentication events (sanitized - never log tokens)
   */
  auth(message: string, details?: any) {
    if (isDevelopment) {
      console.group('[Auth]', message);
      if (details) {
        // Sanitize - never log sensitive data
        const sanitized = { ...details };
        delete sanitized.token;
        delete sanitized.password;
        delete sanitized.access_token;
        console.log(sanitized);
      }
      console.groupEnd();
    }
  }

  /**
   * Log performance metrics
   */
  perf(label: string, duration: number) {
    if (isDevelopment) {
      console.log(`[Perf] ${label}: ${duration.toFixed(2)}ms`);
    }
  }

  /**
   * Create a timer for performance measurement
   */
  time(label: string) {
    if (isDevelopment) {
      console.time(label);
    }
  }

  /**
   * End a timer and log the result
   */
  timeEnd(label: string) {
    if (isDevelopment) {
      console.timeEnd(label);
    }
  }
}

// Export singleton instance
export const logger = new Logger();

// For backward compatibility, export as default
export default logger;
