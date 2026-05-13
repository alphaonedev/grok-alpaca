// Type shim for plotly.js-dist-min — it ships JS only.
// @types/react-plotly.js + @types/plotly.js cover the rest.
declare module "plotly.js-dist-min" {
  const plotly: object;
  export default plotly;
}
