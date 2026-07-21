declare namespace JSX {
  interface Element {}
  interface ElementChildrenAttribute {
    children: {};
  }
  interface IntrinsicElements {
    [name: string]: unknown;
  }
}

declare namespace React {
  type ReactNode = unknown;
}

declare module "react" {
  export type ReactNode = unknown;
  export function useEffect(effect: () => void | (() => void), deps?: readonly unknown[]): void;
  export function useMemo<T>(factory: () => T, deps: readonly unknown[]): T;
  export function useState<T>(initial: T | (() => T)): [T, (next: T | ((current: T) => T)) => void];
  const React: unknown;
  export default React;
}

declare module "react-native" {
  export const Pressable: any;
  export const SafeAreaView: any;
  export const ScrollView: any;
  export const StatusBar: any;
  export const StyleSheet: any;
  export const Switch: any;
  export const Text: any;
  export const TextInput: any;
  export const View: any;
}

declare module "expo" {
  export function registerRootComponent(component: unknown): void;
}
