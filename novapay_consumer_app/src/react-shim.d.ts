declare module "react" {
  export type ReactNode = unknown;
  export function useEffect(effect: () => void | (() => void), deps?: readonly unknown[]): void;
  export function useState<T>(initial: T | (() => T)): [T, (next: T | ((current: T) => T)) => void];
  const React: unknown;
  export default React;
}
