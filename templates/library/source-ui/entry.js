// The actual open-source rendering engines; no canvas imitations of their UI.
import * as monaco from 'monaco-editor/editor/editor.api.js';
import 'monaco-editor/languages/definitions/javascript/register.js';
import { Terminal } from '@xterm/xterm';
import '@xterm/xterm/css/xterm.css';
import '@vscode/codicons/dist/codicon.css';
import * as charts from 'lightweight-charts';
import getTheme from './github-theme/theme.cjs';
import gum from './gum/recording.json';
globalThis.DemoSourceUI = {monaco, Terminal, charts, gum,
  theme: getTheme({theme:'dark', name:'GitHub Dark Default'})};
