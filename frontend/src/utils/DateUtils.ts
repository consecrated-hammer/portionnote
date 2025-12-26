/**
 * Date utilities that handle local timezone correctly
 * Always use these instead of new Date().toISOString()
 */

/**
 * Format a date as YYYY-MM-DD in local timezone
 */
export const FormatLocalDate = (DateObj: Date = new Date()): string => {
  const Year = DateObj.getFullYear();
  const Month = String(DateObj.getMonth() + 1).padStart(2, "0");
  const Day = String(DateObj.getDate()).padStart(2, "0");
  return `${Year}-${Month}-${Day}`;
};

/**
 * Get today's date as YYYY-MM-DD in local timezone
 */
export const GetToday = (): string => FormatLocalDate(new Date());

/**
 * Parse YYYY-MM-DD string to Date object (noon local time to avoid timezone issues)
 */
export const ParseDate = (DateString: string): Date => {
  const [Year, Month, Day] = DateString.split("-").map(Number);
  return new Date(Year, Month - 1, Day, 12, 0, 0, 0);
};

/**
 * Get date N days ago as YYYY-MM-DD
 */
export const GetDaysAgo = (Days: number): string => {
  const DateObj = new Date();
  DateObj.setDate(DateObj.getDate() - Days);
  return FormatLocalDate(DateObj);
};

/**
 * Check if two date strings (YYYY-MM-DD) represent the same day
 */
export const IsSameDay = (Date1: string, Date2: string): boolean => {
  return Date1 === Date2;
};
