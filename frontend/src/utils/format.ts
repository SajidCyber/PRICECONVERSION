/**
 * Safe numeric parsing and formatting utilities
 * Prevents "toFixed is not a function" runtime exceptions
 */

export function num(val: number | string | null | undefined, fallback: number = 0): number {
  if (val === null || val === undefined) return fallback;
  const n = typeof val === 'number' ? val : Number(val);
  return isNaN(n) ? fallback : n;
}

export function fmt(
  val: number | string | null | undefined,
  digits: number = 2,
  fallback: string = '0.00'
): string {
  if (val === null || val === undefined) return fallback;
  const n = typeof val === 'number' ? val : Number(val);
  return isNaN(n) ? fallback : n.toFixed(digits);
}

export function fmtCurrency(
  val: number | string | null | undefined,
  currency: string = 'USD',
  digits: number = 2
): string {
  const formatted = fmt(val, digits);
  return `${currency} ${formatted}`;
}

export function fmtPct(
  val: number | string | null | undefined,
  digits: number = 1,
  showPlus: boolean = true
): string {
  const n = num(val);
  const prefix = showPlus && n > 0 ? '+' : '';
  return `${prefix}${n.toFixed(digits)}%`;
}
