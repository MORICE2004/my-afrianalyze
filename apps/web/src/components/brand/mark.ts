// The AfriEdge mark, drawn on a 48 x 48 grid: the left leg of an "A", its upper right leg, three ascending bars
// (a market rising) and the sweeping edge that cuts across them. Pure geometry in one colour (currentColor), so
// it works on light and dark surfaces and stays legible at favicon size. The static SVG files in public/brand
// are generated from these same paths (scripts/brand.cjs).
export const MARK_VIEWBOX = "0 0 48 48";
export const MARK = {
  leftLeg: "M2 46 L19.5 2 H28 L11.5 46 Z",
  rightLeg: "M28 2 L37.5 23.7 L30.6 27.4 L23.6 10.6 Z",
  edge: "M13 41.5 C22 34.5 33 28.5 46.5 23.5 L46.5 27.2 C34.5 31.2 24.5 36.5 16 43.6 Z",
  bars: [
    { x: 25, y: 41, w: 4.6, h: 5 },
    { x: 32, y: 37, w: 4.6, h: 9 },
    { x: 39, y: 33, w: 4.6, h: 13 },
  ],
} as const;
