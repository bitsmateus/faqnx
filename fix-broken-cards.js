#!/usr/bin/env node
/**
 * Corrige os cards de link quebrados (herdados da importação do GitBook)
 * na Central de Ajuda NX Digital (ajuda.nxsystems.com.br).
 *
 * Uso:
 *   node fix-broken-cards.js            -> dry-run: só mostra o que seria removido
 *   node fix-broken-cards.js --apply    -> aplica de verdade (pede a senha no terminal)
 */
const readline = require('readline');

const SITE = 'https://ajuda.nxsystems.com.br';
const APPLY = process.argv.includes('--apply');
const ANCHOR_RE = /<a\b[^>]*>[\s\S]*?<\/a>/g;

function isBrokenCard(block) {
  return block.includes('ring-tint-subtle') && block.includes('flex-col flex-1');
}
function extractHref(block) {
  const m = block.match(/href="([^"]*)"/);
  return m ? m[1] : '#';
}

// Mesma regra de slug do index.html — permite achar, por um link interno
// (ex.: /instagram-contas-meta), o NOME ATUAL da página que ele aponta.
function slugify(str) {
  return (str || '').normalize('NFD').replace(/[̀-ͯ]/g, '')
    .replace(/[^\w\s-]/g, '').trim().toLowerCase()
    .replace(/\s+/g, '-').replace(/-+/g, '-').replace(/^-+|-+$/g, '');
}
const EMOJI_RE = /[\u{1F000}-\u{1FAFF}\u{2600}-\u{27BF}\u{2B00}-\u{2BFF}\u{1F1E6}-\u{1F1FF}\u{FE0F}\u{20E3}]/gu;
function cleanName(s) { return (s || '').replace(EMOJI_RE, '').replace(/\s{2,}/g, ' ').trim(); }
function buildSlugMap(sections) {
  const used = new Set(), bySlug = {};
  for (const s of sections || []) {
    let base = slugify(s.name) || s.id, slug = base, n = 2;
    while (used.has(slug)) { slug = base + '-' + n; n++; }
    used.add(slug); bySlug[slug] = s;
  }
  return bySlug;
}

// Os cards do GitBook mostram DUAS linhas dentro do link: um título e, embaixo,
// uma legenda com o domínio/URL (ex.: "Comunidade ZDG"). Extrair todo o texto do
// bloco (removendo só as tags) grudava as duas, duplicando a legenda no final
// ("... - Comunidade ZDG Comunidade ZDG") ou colando o caminho cru com o
// domínio ("/instagram-contas-meta ajuda.nxsystems.com.br"). Por isso:
//   1) se o link é interno, prioriza o nome ATUAL da página (sempre certo,
//      inclusive se a página for renomeada depois);
//   2) senão, usa só o primeiro <span> do bloco — é o título, sem a legenda;
//   3) na ausência dessa estrutura, cai no texto puro do bloco inteiro.
function extractLabel(block, href, slugMap) {
  if (href.startsWith('/')) {
    const hit = slugMap[href.slice(1).replace(/\/+$/, '')];
    if (hit) return cleanName(hit.name);
  }
  const spanMatch = block.match(/<span[^>]*>([\s\S]*?)<\/span>/);
  const titulo = spanMatch
    ? spanMatch[1].replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim()
    : '';
  if (titulo) return titulo;
  return block.replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim();
}

function cleanBody(html, slugMap) {
  const removed = [];
  const out = html.replace(ANCHOR_RE, (block) => {
    if (!isBrokenCard(block)) return block;
    const href = extractHref(block), label = extractLabel(block, href, slugMap);
    removed.push({ href, label });
    return `<p><a href="${href}" style="color:var(--brand);text-decoration:underline">${label}</a></p>`;
  });
  return { out, removed };
}
function ask(question) {
  const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
  return new Promise((resolve) => rl.question(question, (a) => { rl.close(); resolve(a); }));
}

async function main() {
  console.log('Buscando conteúdo atual em', SITE + '/api/data ...');
  const res = await fetch(SITE + '/api/data', { cache: 'no-store' });
  if (!res.ok) throw new Error('Falha ao buscar /api/data: ' + res.status);
  const doc = await res.json();
  const slugMap = buildSlugMap(doc.sections);

  let total = 0;
  const report = [];
  for (const sec of doc.sections || []) {
    if (!sec.body) continue;
    const { out, removed } = cleanBody(sec.body, slugMap);
    if (removed.length) { sec.body = out; total += removed.length; report.push({ tipo: 'seção', id: sec.id, nome: sec.name, removidos: removed }); }
  }
  for (const faq of doc.faqs || []) {
    if (!faq.a) continue;
    const { out, removed } = cleanBody(faq.a, slugMap);
    if (removed.length) { faq.a = out; total += removed.length; report.push({ tipo: 'FAQ', id: faq.id, nome: faq.q, removidos: removed }); }
  }

  console.log(`\nEncontrados ${total} card(s) quebrado(s) em ${report.length} página(s):\n`);
  for (const r of report) {
    console.log(`- [${r.tipo}] ${r.nome} (${r.id})`);
    for (const rm of r.removidos) console.log(`    -> vira link: "${rm.label}" -> ${rm.href}`);
  }

  if (!APPLY) { console.log('\nDry-run: nada foi salvo. Rode com --apply para gravar de verdade.'); return; }
  if (total === 0) { console.log('\nNada para corrigir.'); return; }

  const pw = await ask('\nSenha do admin: ');
  const loginRes = await fetch(SITE + '/api/login', {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ password: pw }),
  });
  if (!loginRes.ok) throw new Error('Login falhou: ' + loginRes.status);
  const { token } = await loginRes.json();

  if (typeof doc.version === 'number') doc.version += 1;

  const saveRes = await fetch(SITE + '/api/save', {
    method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: 'Bearer ' + token }, body: JSON.stringify(doc),
  });
  if (!saveRes.ok) throw new Error('Save falhou: ' + saveRes.status);
  console.log('\nSalvo com sucesso —', total, 'card(s) quebrado(s) viraram links de texto normais.');
}
main().catch((e) => { console.error('Erro:', e.message); process.exit(1); });
