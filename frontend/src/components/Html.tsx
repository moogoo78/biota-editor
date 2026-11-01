/** Render TaiCOL markup safely: only <i>, <b>, <br> survive; everything else is text. */
const ALLOWED = /^<\/?(i|b|br)\s*\/?>$/i;

export function safeHtml(s: string | null | undefined): string {
  if (!s) return "";
  return s
    .split(/(<[^>]*>)/g)
    .map((part) => {
      if (ALLOWED.test(part)) return part.toLowerCase().replace(/\s+/g, "").replace("<br/>", "<br>");
      return part.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    })
    .join("");
}

export default function Html({ html, as: Tag = "span", className }: {
  html: string | null | undefined; as?: "span" | "div" | "p"; className?: string;
}) {
  return <Tag className={className} dangerouslySetInnerHTML={{ __html: safeHtml(html) }} />;
}
