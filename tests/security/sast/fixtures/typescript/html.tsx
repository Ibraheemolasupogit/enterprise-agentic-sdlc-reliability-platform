// C5-M05 HTML/eval controls. Synthetic; never rendered.
export function UnsafeHtml({ body }: { body: string }) {
  // ruleid: morrow.ts.unsafe-html-or-eval
  return <div dangerouslySetInnerHTML={{ __html: body }} />;
}

export function unsafeDom(el: HTMLElement, body: string) {
  // ruleid: morrow.ts.unsafe-html-or-eval
  el.innerHTML = body;
}

export function unsafeEval(expression: string) {
  // ruleid: morrow.ts.unsafe-html-or-eval
  return eval(expression);
}

export function unsafeFunction(source: string) {
  // ruleid: morrow.ts.unsafe-html-or-eval
  return new Function("value", source);
}

export function SafeText({ body }: { body: string }) {
  // ok: morrow.ts.unsafe-html-or-eval
  return <p className="note">{body}</p>;
}

export function safeDom(el: HTMLElement, body: string) {
  // ok: morrow.ts.unsafe-html-or-eval
  el.textContent = body;
}
