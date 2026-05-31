/** 从 Content-Disposition 解析文件名（无业务文案硬编码） */
export function parseContentDispositionFilename(header: string | null): string | null {
  if (!header) return null;
  const utf8Match = /filename\*=UTF-8''([^;\s]+)/i.exec(header);
  if (utf8Match?.[1]) {
    try {
      return decodeURIComponent(utf8Match[1]);
    } catch {
      return utf8Match[1];
    }
  }
  const quoted = /filename="([^"]+)"/i.exec(header);
  if (quoted?.[1]) return quoted[1];
  const plain = /filename=([^;\s]+)/i.exec(header);
  if (plain?.[1]) return plain[1].replace(/^["']|["']$/g, "");
  return null;
}
