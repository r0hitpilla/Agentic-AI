// Parse every ```mermaid block in the given markdown files with the real Mermaid parser.
import { JSDOM } from 'jsdom';
import fs from 'node:fs';

const dom = new JSDOM('<!doctype html><html><body></body></html>', { pretendToBeVisual: true });
globalThis.window = dom.window;
globalThis.document = dom.window.document;
globalThis.DOMParser = dom.window.DOMParser;
globalThis.Element = dom.window.Element;
globalThis.HTMLElement = dom.window.HTMLElement;
globalThis.SVGElement = dom.window.SVGElement;

const { default: mermaid } = await import('mermaid');
mermaid.initialize({ startOnLoad: false });

let total = 0, failed = 0;
for (const file of process.argv.slice(2)) {
  const text = fs.readFileSync(file, 'utf8');
  const re = /```mermaid\n([\s\S]*?)```/g;
  let m, i = 0;
  while ((m = re.exec(text))) {
    i++; total++;
    const line = text.slice(0, m.index).split('\n').length;
    try {
      await mermaid.parse(m[1]);
    } catch (e) {
      failed++;
      console.log(`FAIL ${file} block ${i} (line ${line}): ${String(e.message || e).split('\n').slice(0, 4).join(' | ')}`);
    }
  }
}
console.log(`${total} diagrams parsed, ${failed} failed`);
process.exit(failed ? 1 : 0);
