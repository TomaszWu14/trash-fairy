// Własna paczka ECharts (zamiast pełnej 1 MB): tylko używane wykresy i komponenty, renderer SVG.
// Budowanie: npm i echarts@5.6.0 esbuild && npx esbuild scripts/echarts-entry.js --bundle --minify --format=iife --legal-comments=none --outfile=app/static/vendor/echarts/echarts.min.js
import * as echarts from 'echarts/core';
import { LineChart, BarChart, PieChart, HeatmapChart } from 'echarts/charts';
import { GridComponent, TooltipComponent, LegendComponent, MarkLineComponent, VisualMapComponent, GraphicComponent, AriaComponent, TitleComponent } from 'echarts/components';
import { SVGRenderer } from 'echarts/renderers';
echarts.use([LineChart, BarChart, PieChart, HeatmapChart, GridComponent, TooltipComponent, LegendComponent, MarkLineComponent,
  VisualMapComponent, GraphicComponent, AriaComponent, TitleComponent, SVGRenderer]);
window.echarts = echarts;
