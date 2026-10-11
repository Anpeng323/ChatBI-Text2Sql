import React from "react";

/**
 * 轻量 Markdown 渲染器（零依赖）。
 * 支持：标题(#~######)、粗体(**)、斜体(*)、行内代码(`)、代码块(```)、
 * 无序/有序列表、表格、引用、水平分割线、链接。
 * 面向 LLM 回答的常见子集，按深色主题排版。
 */

/** 解析行内标记：**粗体**、*斜体*、`代码`、[文本](链接)。 */
function parseInline(text: string, keyPrefix: string): React.ReactNode[] {
  const nodes: React.ReactNode[] = [];
  const regex = /(\*\*[^*]+\*\*|`[^`]+`|\*[^*]+\*|\[[^\]]+\]\([^)]+\))/g;
  let last = 0;
  let m: RegExpExecArray | null;
  let idx = 0;
  while ((m = regex.exec(text)) !== null) {
    if (m.index > last) nodes.push(text.slice(last, m.index));
    const token = m[0];
    const k = `${keyPrefix}-${idx++}`;
    if (token.startsWith("**")) {
      nodes.push(
        <strong key={k} className="font-semibold text-txt-hi">
          {token.slice(2, -2)}
        </strong>
      );
    } else if (token.startsWith("`")) {
      nodes.push(
        <code
          key={k}
          className="rounded bg-black/40 px-1.5 py-0.5 font-mono text-[12.5px] text-brand-teal"
        >
          {token.slice(1, -1)}
        </code>
      );
    } else if (token.startsWith("[")) {
      const mm = /\[([^\]]+)\]\(([^)]+)\)/.exec(token);
      if (mm) {
        nodes.push(
          <a
            key={k}
            href={mm[2]}
            target="_blank"
            rel="noreferrer"
            className="text-brand-blue underline decoration-brand-blue/40 hover:decoration-brand-blue"
          >
            {mm[1]}
          </a>
        );
      } else {
        nodes.push(token);
      }
    } else {
      nodes.push(
        <em key={k} className="italic text-txt-mid">
          {token.slice(1, -1)}
        </em>
      );
    }
    last = m.index + token.length;
  }
  if (last < text.length) nodes.push(text.slice(last));
  return nodes;
}

const HEADING: Record<number, string> = {
  1: "mt-4 mb-2 text-[19px] font-semibold text-txt-hi",
  2: "mt-4 mb-2 text-[16.5px] font-semibold text-txt-hi",
  3: "mt-3.5 mb-1.5 text-[14.5px] font-semibold text-brand-teal",
  4: "mt-3 mb-1.5 text-[13.5px] font-semibold text-txt-hi",
  5: "mt-2.5 mb-1 text-[13px] font-semibold text-txt-hi",
  6: "mt-2.5 mb-1 text-[12.5px] font-semibold text-txt-mid",
};

export default function Markdown({ text }: { text: string }) {
  const lines = text.replace(/\r\n/g, "\n").split("\n");
  const blocks: React.ReactNode[] = [];
  let i = 0;
  let key = 0;

  const parseRow = (l: string) =>
    l.trim().replace(/^\|/, "").replace(/\|$/, "").split("|").map((c) => c.trim());

  while (i < lines.length) {
    const line = lines[i];

    // 代码块 ```lang ... ```
    const fence = /^\s*```/.exec(line);
    if (fence) {
      const buf: string[] = [];
      i++;
      while (i < lines.length && !/^\s*```/.test(lines[i])) {
        buf.push(lines[i]);
        i++;
      }
      i++; // 跳过结尾 ```
      blocks.push(
        <pre
          key={key++}
          className="overflow-x-auto rounded-lg border border-white/5 bg-black/40 p-3 text-[12.5px] leading-relaxed text-txt-mid"
        >
          <code>{buf.join("\n")}</code>
        </pre>
      );
      continue;
    }

    // 空行
    if (/^\s*$/.test(line)) {
      i++;
      continue;
    }

    // 标题（兼容 ###无空格 的写法）
    const h = /^(#{1,6})\s*(.+)$/.exec(line);
    if (h) {
      const level = h[1].length;
      blocks.push(
        <div key={key++} className={HEADING[level]}>
          {parseInline(h[2], `h${key}`)}
        </div>
      );
      i++;
      continue;
    }

    // 水平分割线
    if (/^\s*([-*_])\1{2,}\s*$/.test(line)) {
      blocks.push(<hr key={key++} className="my-3 border-white/10" />);
      i++;
      continue;
    }

    // 表格（下一行是分隔行）
    if (
      line.includes("|") &&
      i + 1 < lines.length &&
      /^\s*\|?\s*:?-+:?\s*(\|\s*:?-+:?\s*)+\|?\s*$/.test(lines[i + 1])
    ) {
      const header = parseRow(line);
      i += 2;
      const rows: string[][] = [];
      while (i < lines.length && lines[i].includes("|") && !/^\s*$/.test(lines[i])) {
        rows.push(parseRow(lines[i]));
        i++;
      }
      blocks.push(
        <div key={key++} className="overflow-x-auto">
          <table className="w-full border-collapse text-[12.5px]">
            <thead>
              <tr>
                {header.map((c, ci) => (
                  <th
                    key={ci}
                    className="border-b border-white/10 px-2.5 py-1.5 text-left font-semibold text-txt-hi"
                  >
                    {parseInline(c, `th${ci}`)}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((r, ri) => (
                <tr key={ri} className="odd:bg-white/[0.02]">
                  {r.map((c, ci) => (
                    <td key={ci} className="border-b border-white/5 px-2.5 py-1.5 text-txt-mid">
                      {parseInline(c, `td${ri}-${ci}`)}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      );
      continue;
    }

    // 无序列表 - / * / +
    if (/^\s*[-*+]\s+/.test(line)) {
      const items: string[] = [];
      while (i < lines.length && /^\s*[-*+]\s+/.test(lines[i])) {
        items.push(lines[i].replace(/^\s*[-*+]\s+/, ""));
        i++;
      }
      blocks.push(
        <ul key={key++} className="my-1 ml-5 list-disc space-y-1 text-txt-hi marker:text-brand-teal/70">
          {items.map((it, ii) => (
            <li key={ii} className="leading-relaxed">
              {parseInline(it, `ul${key}-${ii}`)}
            </li>
          ))}
        </ul>
      );
      continue;
    }

    // 有序列表 1. 2.
    if (/^\s*\d+\.\s+/.test(line)) {
      const items: string[] = [];
      while (i < lines.length && /^\s*\d+\.\s+/.test(lines[i])) {
        items.push(lines[i].replace(/^\s*\d+\.\s+/, ""));
        i++;
      }
      blocks.push(
        <ol key={key++} className="my-1 ml-5 list-decimal space-y-1 text-txt-hi marker:text-brand-teal/70">
          {items.map((it, ii) => (
            <li key={ii} className="leading-relaxed">
              {parseInline(it, `ol${key}-${ii}`)}
            </li>
          ))}
        </ol>
      );
      continue;
    }

    // 引用 >
    if (/^\s*>\s?/.test(line)) {
      const buf: string[] = [];
      while (i < lines.length && /^\s*>\s?/.test(lines[i])) {
        buf.push(lines[i].replace(/^\s*>\s?/, ""));
        i++;
      }
      blocks.push(
        <blockquote
          key={key++}
          className="my-1 border-l-2 border-brand-teal/50 pl-3 text-txt-mid"
        >
          {parseInline(buf.join(" "), `bq${key}`)}
        </blockquote>
      );
      continue;
    }

    // 段落：合并连续的普通行
    const buf: string[] = [line];
    i++;
    while (
      i < lines.length &&
      !/^\s*$/.test(lines[i]) &&
      !/^#{1,6}\s*\S/.test(lines[i]) &&
      !/^\s*[-*+]\s+/.test(lines[i]) &&
      !/^\s*\d+\.\s+/.test(lines[i]) &&
      !/^\s*```/.test(lines[i]) &&
      !/^\s*>/.test(lines[i]) &&
      !/^\s*([-*_])\1{2,}\s*$/.test(lines[i])
    ) {
      buf.push(lines[i]);
      i++;
    }
    blocks.push(
      <p key={key++} className="leading-relaxed text-txt-hi">
        {parseInline(buf.join(" "), `p${key}`)}
      </p>
    );
  }

  return <div className="space-y-1.5">{blocks}</div>;
}
