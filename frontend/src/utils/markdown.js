const ESCAPE_MAP = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }

const escapeHtml = (value = '') => String(value).replace(/[&<>"']/g, (char) => ESCAPE_MAP[char] || char)

export const renderSafeMarkdown = (content) => {
  if (!content) return ''

  let processedContent = escapeHtml(String(content)).replace(/^##\s+.+\n+/, '')
  let html = processedContent.replace(/```(\w*)\n([\s\S]*?)```/g, '<pre class="code-block"><code>$2</code></pre>')
  html = html.replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>')
  html = html.replace(/^#### (.+)$/gm, '<h5 class="md-h5">$1</h5>')
  html = html.replace(/^### (.+)$/gm, '<h4 class="md-h4">$1</h4>')
  html = html.replace(/^## (.+)$/gm, '<h3 class="md-h3">$1</h3>')
  html = html.replace(/^# (.+)$/gm, '<h2 class="md-h2">$1</h2>')
  html = html.replace(/^> (.+)$/gm, '<blockquote class="md-quote">$1</blockquote>')
  html = html.replace(/^(\s*)- (.+)$/gm, (match, indent, text) => `<li class="md-li" data-level="${Math.floor(indent.length / 2)}">${text}</li>`)
  html = html.replace(/^(\s*)(\d+)\. (.+)$/gm, (match, indent, num, text) => `<li class="md-oli" data-level="${Math.floor(indent.length / 2)}">${text}</li>`)
  html = html.replace(/(<li class="md-li"[^>]*>.*?<\/li>\s*)+/g, '<ul class="md-ul">$&</ul>')
  html = html.replace(/(<li class="md-oli"[^>]*>.*?<\/li>\s*)+/g, '<ol class="md-ol">$&</ol>')
  html = html.replace(/<\/li>\s+<li/g, '</li><li')
  html = html.replace(/<ul class="md-ul">\s+/g, '<ul class="md-ul">')
  html = html.replace(/<ol class="md-ol">\s+/g, '<ol class="md-ol">')
  html = html.replace(/\s+<\/ul>/g, '</ul>')
  html = html.replace(/\s+<\/ol>/g, '</ol>')
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
  html = html.replace(/\*(.+?)\*/g, '<em>$1</em>')
  html = html.replace(/_(.+?)_/g, '<em>$1</em>')
  html = html.replace(/\n\n+/g, '</p><p class="md-p">')
  html = html.replace(/\n/g, '<br>')
  if (!/^<(h\d|p|ul|ol|blockquote|pre)/.test(html)) {
    html = `<p class="md-p">${html}</p>`
  }
  html = html.replace(/<p class="md-p"><\/p>/g, '')
  html = html.replace(/<p class="md-p">\s*(<(h\d|ul|ol|blockquote|pre))/g, '$1')
  html = html.replace(/(<\/h\d>|<\/ul>|<\/ol>|<\/blockquote>|<\/pre>)\s*<\/p>/g, '$1')
  return html
}
