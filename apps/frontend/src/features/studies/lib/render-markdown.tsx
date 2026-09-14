import type { ReactNode } from "react";

/** Satır içi (**kalın**) metni React düğümlerine çevirir. */
export function parseBoldText(text: string): ReactNode[] {
  const parts = text.split(/\*\*([^*]+)\*\*/g);
  return parts.map((part, index) => {
    // Every odd element is bold
    if (index % 2 === 1) {
      return <strong key={index} className="font-semibold text-primary dark:text-border-light">{part}</strong>;
    }
    return part;
  });
}

/**
 * Harici bağımlılık olmadan sentez raporu markdown'ını React düğümlerine çeviren
 * hafif ayrıştırıcı (refactor R2-8). Davranış R2 öncesiyle birebir aynıdır.
 */
export function renderMarkdown(mdText?: string): ReactNode {
  if (!mdText) return <p className="text-muted-foreground">Rapor içeriği bulunmamaktadır.</p>;

  const lines = mdText.split("\n");
  const out: ReactNode[] = [];
  let i = 0;

  const renderTable = (startIdx: number): number => {
    // startIdx bir tablo satırı ("| ... |") — ardışık satırları topla
    const rows: string[][] = [];
    let j = startIdx;
    while (j < lines.length && lines[j].trim().startsWith("|")) {
      const cells = lines[j].trim().split("|").slice(1, -1).map((c) => c.trim());
      // Ayraç satırını (|---|) atla
      if (!cells.every((c) => /^:?-{2,}:?$/.test(c))) {
        rows.push(cells);
      }
      j++;
    }
    if (rows.length === 0) return j;
    const [head, ...body] = rows;
    out.push(
      <div key={`tbl-${startIdx}`} className="overflow-x-auto my-4 border border-hairline dark:border-canvas/10 rounded-lg">
        <table className="w-full text-sm">
          {head && (
            <thead>
              <tr className="bg-muted-surface dark:bg-canvas/5">
                {head.map((c, ci) => (
                  <th key={ci} className="text-left font-bold text-ink dark:text-border-light px-3 py-2 border-b border-hairline">{c}</th>
                ))}
              </tr>
            </thead>
          )}
          <tbody>
            {body.map((row, ri) => (
              <tr key={ri} className="border-b border-soft-stone last:border-0">
                {row.map((c, ci) => (
                  <td key={ci} className="px-3 py-2 text-body-muted dark:text-slate-soft">{parseBoldText(c)}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
    return j;
  };

  while (i < lines.length) {
    const line = lines[i];
    const idx = i;

    // Tablo satırı — ardışık tablo satırlarını tek bileşene topla
    if (line.trim().startsWith("|")) {
      i = renderTable(i);
      continue;
    }

    // Headers
    if (line.startsWith("### ")) {
      out.push(<h4 key={idx} className="text-lg font-semibold text-ink dark:text-border-light mt-5 mb-2">{line.replace("### ", "")}</h4>);
      i++;
      continue;
    }
    if (line.startsWith("## ")) {
      out.push(<h3 key={idx} className="text-xl font-bold text-ink dark:text-border-light mt-6 mb-3 border-b pb-1 border-hairline dark:border-canvas/10">{line.replace("## ", "")}</h3>);
      i++;
      continue;
    }
    if (line.startsWith("# ")) {
      out.push(<h2 key={idx} className="text-2xl font-black text-primary dark:text-white mt-8 mb-4">{line.replace("# ", "")}</h2>);
      i++;
      continue;
    }

    // Bullet points
    if (line.trim().startsWith("- ") || line.trim().startsWith("* ")) {
      const cleanText = line.trim().replace(/^[-*]\s+/, "");
      out.push(
        <li key={idx} className="list-disc pl-2 ml-5 text-body-muted leading-relaxed my-1">
          {parseBoldText(cleanText)}
        </li>
      );
      i++;
      continue;
    }

    // Blockquotes / Warnings
    if (line.startsWith("> ")) {
      out.push(
        <div key={idx} className="border-l-4 border-action-blue pl-4 py-2 bg-pale-blue/40 dark:bg-dark-navy/20 rounded-r-md text-body-muted italic my-4">
          {line.replace("> ", "")}
        </div>
      );
      i++;
      continue;
    }

    // Paragraph
    if (line.trim() === "") {
      i++;
      continue;
    }

    out.push(
      <p key={idx} className="text-body-muted leading-relaxed my-3">
        {parseBoldText(line)}
      </p>
    );
    i++;
  }

  return out;
}
