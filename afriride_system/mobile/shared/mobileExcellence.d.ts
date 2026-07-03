export type AdaptiveClass = "compact" | "medium" | "expanded";

export function useMobileExcellence(): {
  width: number;
  height: number;
  fontScale: number;
  reduceMotion: boolean;
  adaptiveClass: AdaptiveClass;
  isFoldablePosture: boolean;
  theme: {
    dark: boolean;
    primary: any;
    background: string;
    surface: string;
    onSurface: string;
    outline: string;
  };
};

export function AdaptiveScaffold(props: {
  children?: any;
  navigation?: any;
  testID?: string;
  brandColor?: string;
}): any;

export function AnimatedEntrance(props: { children?: any; style?: any }): any;
export function SkeletonBlock(props: { height?: number }): any;
export function SyncBanner(props: { online: boolean; pending: number }): any;
