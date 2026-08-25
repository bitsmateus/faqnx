// ═══════════════════════════════════════════════════════════
// Central de Ajuda NX Digital — backend Express + Postgres
// ═══════════════════════════════════════════════════════════
const express = require('express');
const compression = require('compression');
const path = require('path');
const fs = require('fs');
const crypto = require('crypto');
const { Pool } = require('pg');

const PORT = process.env.PORT || 80;
const DATABASE_URL = process.env.DATABASE_URL;

if (!DATABASE_URL) {
  console.error('ERRO: variável de ambiente DATABASE_URL não definida.');
  process.exit(1);
}

const pool = new Pool({ connectionString: DATABASE_URL });

// tokens de admin válidos em memória (resetam ao reiniciar o container)
const tokens = new Set();

// ─── Inicializa o banco e popula com o seed na 1ª execução ───
async function initDb() {
  await pool.query(`
    CREATE TABLE IF NOT EXISTS store (
      id INT PRIMARY KEY,
      doc JSONB NOT NULL,
      updated_at TIMESTAMPTZ DEFAULT now()
    );
  `);
  await pool.query(`
    CREATE TABLE IF NOT EXISTS images (
      id TEXT PRIMARY KEY,
      mime TEXT NOT NULL,
      data BYTEA NOT NULL,
      created_at TIMESTAMPTZ DEFAULT now()
    );
  `);
  const { rows } = await pool.query('SELECT 1 FROM store WHERE id = 1');
  if (rows.length === 0) {
    const seed = JSON.parse(fs.readFileSync(path.join(__dirname, 'seed.json'), 'utf8'));
    await pool.query('INSERT INTO store (id, doc) VALUES (1, $1)', [seed]);
    console.log('Banco populado com o conteúdo inicial (seed.json).');
  } else {
    console.log('Banco já contém dados — seed ignorado.');
  }
  try { await migrateInlineImages(); } catch (e) { console.error('Falha na migração de imagens:', e); }
  try { await migrateBrand(); } catch (e) { console.error('Falha na migração de marca:', e); }
  try { await migrateHelpLinks(); } catch (e) { console.error('Falha na migração de links:', e); }
}

// Troca toda menção a Z-PRO / ZPRO / z-pro / zpro por "NX Digital" no conteúdo salvo.
// Palavra inteira e sem separador com espaço, para não afetar palavras como "processo" ou "voz pro".
async function migrateBrand() {
  const doc = await getDoc();
  if (!doc) return;
  const json = JSON.stringify(doc);
  const re = /(?<![a-zA-Z0-9])z[-_]?pro(?![a-zA-Z0-9])/gi;
  const matches = json.match(re);
  if (!matches) return;
  const out = json.replace(re, 'NX Digital');
  await setDoc(JSON.parse(out));
  console.log('Marca: substituídas ' + matches.length + ' ocorrência(s) de Z-PRO por "NX Digital".');
}

// ─── Migração de links internos ───
// O conteúdo veio do GitBook da ZDG, então os links de "veja também" ainda
// apontavam para ajuda.zdg.com.br e tiravam o visitante da nossa central.
// Aqui cada link vira um caminho interno (/slug-da-secao#ancora), usando o
// mesmo slug que o front-end gera a partir do nome da seção.
// As imagens (/~gitbook/image) não são tocadas — só links de navegação.
const HELP_HOST = 'ajuda.nxsystems.com.br';

// Páginas da ZDG cujo endereço não bate com o nome da nossa seção
// (ou que não existem aqui e vão para a página equivalente mais próxima).
const LINK_ALIAS = {
  'equipes': 'equipe',
  'tela-de-atendimento': 'tela-de-atendimentos',
  'barra-de-mensagem': 'tela-de-atendimentos',
  'wavoip': 'wavoip-gestao-comercial',
  'webchat': 'habilitar-webchat',
  'whatsapp-oficial-oauth-app-nx': 'whatsapp-oficial-oauth-app-nx-digital-com-coexistencia',
  'whatsapp-oficial-oauth-login': 'whatsapp-oficial-oauth-app-nx-digital-com-coexistencia',
  'api-oficial-cadastro-incorporado-e-coexistencia-waba-beta': 'whatsapp-oficial-oauth-app-nx-digital-com-coexistencia',
  'canal-dialog360-bsp': 'bsp-dialog360-e-gupshup',
  'canal-gupshup-bsp': 'bsp-dialog360-e-gupshup',
  'instalacao-evolution-api': 'canal-evolution-api-nao-oficial',
  'proxy-ipv4-no-proxy-seller': 'canais-de-comunicacao',
  'api': 'api-configuracoes',
  'referencia-da-api': 'api-configuracoes',
  'waba-interativo': 'atendimento-waba-api-oficial',
  'api-oficial-waba': 'whatsapp-oficial-via-api-cloud-waba',
  'api-oficial-do-whatsapp-vs-apis-nao-oficiais': 'whatsapp-oficial-via-api-cloud-waba',
  'cobrancas-da-meta-whatsapp-business-platform': 'whatsapp-oficial-via-api-cloud-waba',
  'ligacoes-no-nx': 'ligacoes-no-nx-digital-telefonia-e-voz',
  'ligacoes-de-voz-na-api-oficial-waba': 'ligacoes-no-nx-digital-telefonia-e-voz',
  'funil-de-oportunidades': 'funil-de-vendas',
  'configuracao': 'configuracoes-painel-admin',
  'log-de-auditoria': 'log-auditoria-admin',
  'linkedin-superadmin': 'linkedin-configuracao-apps',
  'mercado-livre-superadmin': 'mercado-livre-configuracao-apps',
  'olx-superadmin': 'olx-configuracao-apps',
  'tiktok-superadmin': 'tiktok-configuracao-apps',
  'woocommerce-superadmin': 'woocommerce-configuracao-apps',
  'google-superadmin': 'google-configuracao-apps',
  'rocketchat-superadmin': 'rocketchat-configuracao-apps',
  'facebook-login-incorporado-waba-insta-messenger': 'instagram-e-facebook-messenger-via-oauth-login',
  'canal-facebook-messenger-nativo-beta': 'facebook-contas-meta',
  'canal-instagram-nativo-beta': 'instagram-contas-meta',
  'gerenciar-licenca-nx': 'visao-geral-admin',
  'como-funciona-o-nx': '',          // '' = home
  'conheca-o-nx-digital': '',
};

// mesma regra de slug do front-end (index.html), para os links baterem com as URLs reais
function slugifyName(str) {
  return (str || '').normalize('NFD').replace(/[̀-ͯ]/g, '')
    .replace(/[^\w\s-]/g, '').trim().toLowerCase()
    .replace(/\s+/g, '-').replace(/-+/g, '-').replace(/^-+|-+$/g, '');
}

// Devolve uma função que traduz um pedaço da URL antiga no slug da nossa seção.
// Tenta, em ordem: apelido conhecido → slug exato → sem hífens → sem a marca.
function buildSectionResolver(sections) {
  const bySlug = {}, flat = {}, noBrand = {};
  const used = new Set();
  (sections || []).forEach(s => {
    let base = (s.slug && slugifyName(s.slug)) || slugifyName(s.name) || s.id;
    if (!base) base = s.id;
    let slug = base, n = 2;
    while (used.has(slug)) { slug = base + '-' + n; n++; }
    used.add(slug);
    bySlug[slug] = true;
  });
  const brand = /nxdigital|nx|zdg|zpro/g;
  const put = (o, k, v) => { o[k] = o[k] === undefined ? v : null; };   // null = ambíguo, não serve
  Object.keys(bySlug).forEach(slug => {
    const f = slug.replace(/-/g, '');
    put(flat, f, slug);
    put(noBrand, f.replace(brand, ''), slug);
  });
  return function resolveSegment(segment) {
    const key = slugifyName(segment);
    if (LINK_ALIAS[key] !== undefined) return LINK_ALIAS[key];
    if (bySlug[key]) return key;
    const f = key.replace(/-/g, '');
    if (flat[f]) return flat[f];
    const b = noBrand[f.replace(brand, '')];
    if (b) return b;
    return null;
  };
}

// URL antiga -> caminho interno. Se a página exata não existir aqui, sobe para
// a categoria pai da URL; em último caso cai na home.
function helpUrlToInternal(url, resolveSegment) {
  let rest = url.slice(url.indexOf('zdg.com.br') + 'zdg.com.br'.length);
  const h = rest.indexOf('#');
  const hash = h >= 0 ? rest.slice(h) : '';
  if (h >= 0) rest = rest.slice(0, h);
  rest = rest.split('?')[0].replace(/[/]+$/, '');
  const segs = rest.split('/').filter(Boolean).map(x => {
    try { return decodeURIComponent(x); } catch (e) { return x; }
  });
  for (let i = segs.length - 1; i >= 0; i--) {
    const target = resolveSegment(segs[i]);
    if (target !== null) return (target ? '/' + target : '/') + hash;
  }
  return '/' + hash;
}

async function migrateHelpLinks() {
  const doc = await getDoc();
  if (!doc) return;
  const resolveSegment = buildSectionResolver(doc.sections);
  const json = JSON.stringify(doc);
  let n = 0;

  // 1) links embrulhados em redirect do Google (google.com/url?...q=<url antiga>)
  const RE_GOOGLE = /https:[/][/]www[.]google[.]com[/]url[?][A-Za-z0-9_.~%#?&=+:*/ -]*ajuda[.]zdg[.]com[.]br[A-Za-z0-9_.~%#?&=+:*/ -]*/g;
  let out = json.replace(RE_GOOGLE, (m) => {
    const i = m.indexOf('ajuda.zdg.com.br');
    if (i < 0) return m;
    n++;
    return helpUrlToInternal(decodeURIComponent(m.slice(i).replace(/ /g, '%20')), resolveSegment);
  });

  // 2) links diretos para a central antiga. O " Digital" no meio do caminho existe
  //    porque a migração de marca trocou "Z-PRO" por "NX Digital" dentro das URLs.
  const RE_LINK = /https:[/][/]ajuda[.]zdg[.]com[.]br(?![/]~gitbook)(?:[A-Za-z0-9_.~%#?&=+:*/-]| Digital)*/g;
  out = out.replace(RE_LINK, (m) => { n++; return helpUrlToInternal(m, resolveSegment); });

  // 3) o domínio antigo aparecendo como texto visível
  out = out.replace(/ajuda[.]zdg[.]com[.]br(?![/]~gitbook)/g, () => { n++; return HELP_HOST; });

  if (out === json) return;   // nada a migrar (já rodou antes)
  await setDoc(JSON.parse(out));
  console.log('Links: ' + n + ' link(s) da central antiga passaram a apontar para páginas internas.');
}

// Migra imagens embutidas em base64 (data:) para a tabela images, trocando por links leves.
// Roda uma vez: depois de migrar não sobra nenhum data:image, então não repete.
async function migrateInlineImages() {
  const doc = await getDoc();
  if (!doc) return;
  const json = JSON.stringify(doc);
  if (json.indexOf('data:image/') === -1) return;   // nada a migrar
  const re = /data:(image\/[a-zA-Z0-9.+-]+);base64,([A-Za-z0-9+/=]+)/g;
  const map = new Map();
  let m;
  while ((m = re.exec(json)) !== null) {
    if (map.has(m[0])) continue;
    const id = crypto.randomUUID().replace(/-/g, '');
    const buf = Buffer.from(m[2], 'base64');
    await pool.query('INSERT INTO images (id, mime, data) VALUES ($1, $2, $3)', [id, m[1], buf]);
    map.set(m[0], '/api/img/' + id);
  }
  if (map.size === 0) return;
  const out = json.replace(re, s => map.get(s) || s);
  await setDoc(JSON.parse(out));
  console.log('Migradas ' + map.size + ' imagem(ns) base64 para o banco (conteúdo agora usa links leves).');
}

async function getDoc() {
  const { rows } = await pool.query('SELECT doc FROM store WHERE id = 1');
  return rows[0] ? rows[0].doc : null;
}

async function setDoc(doc) {
  await pool.query(
    'UPDATE store SET doc = $1, updated_at = now() WHERE id = 1',
    [doc]
  );
}

// ─── App ───
const app = express();
app.use(compression()); // gzip: reduz muito o tamanho do HTML e da API
app.use(express.json({ limit: '50mb' }));

// Conteúdo público (sem a senha do admin)
app.get('/api/data', async (req, res) => {
  try {
    const doc = await getDoc();
    if (!doc) return res.status(503).json({ error: 'sem dados' });
    const safe = JSON.parse(JSON.stringify(doc));
    if (safe.settings) delete safe.settings.pw;
    res.set('Cache-Control', 'no-store, no-cache, must-revalidate');
    res.json(safe);
  } catch (e) {
    console.error(e);
    res.status(500).json({ error: 'erro ao buscar dados' });
  }
});

// Login do admin
app.post('/api/login', async (req, res) => {
  try {
    const { password } = req.body || {};
    const doc = await getDoc();
    const pw = (doc && doc.settings && doc.settings.pw) || 'nx@admin2024';
    if (password && password === pw) {
      const token = crypto.randomUUID();
      tokens.add(token);
      return res.json({ token });
    }
    res.status(401).json({ error: 'senha incorreta' });
  } catch (e) {
    console.error(e);
    res.status(500).json({ error: 'erro no login' });
  }
});

function requireAuth(req, res, next) {
  const auth = req.headers.authorization || '';
  const token = auth.replace(/^Bearer\s+/i, '');
  if (token && tokens.has(token)) return next();
  res.status(401).json({ error: 'não autorizado' });
}

// Salvar conteúdo (somente admin autenticado)
app.post('/api/save', requireAuth, async (req, res) => {
  try {
    const incoming = req.body;
    if (!incoming || !incoming.sections || !incoming.faqs) {
      return res.status(400).json({ error: 'dados inválidos' });
    }
    // preserva a senha atual se a nova vier vazia (o GET remove a senha)
    const current = await getDoc();
    const currentPw = (current && current.settings && current.settings.pw) || 'nx@admin2024';
    if (!incoming.settings) incoming.settings = {};
    if (!incoming.settings.pw) incoming.settings.pw = currentPw;
    await setDoc(incoming);
    res.json({ ok: true });
  } catch (e) {
    console.error(e);
    res.status(500).json({ error: 'erro ao salvar' });
  }
});

// Upload de imagem (somente admin) — guarda a imagem no banco e devolve uma URL curta.
// Assim o conteúdo salvo fica leve (só o link), em vez de imagens gigantes em base64.
app.post('/api/upload', requireAuth, express.raw({ type: () => true, limit: '25mb' }), async (req, res) => {
  try {
    const mime = (req.headers['content-type'] || 'application/octet-stream').split(';')[0].trim();
    if (!mime.startsWith('image/')) return res.status(400).json({ error: 'o arquivo não é uma imagem' });
    const buf = req.body;
    if (!buf || !buf.length) return res.status(400).json({ error: 'imagem vazia' });
    const id = crypto.randomUUID().replace(/-/g, '');
    await pool.query('INSERT INTO images (id, mime, data) VALUES ($1, $2, $3)', [id, mime, buf]);
    res.json({ url: '/api/img/' + id });
  } catch (e) {
    console.error('upload', e);
    res.status(500).json({ error: 'erro ao salvar a imagem' });
  }
});

// Servir imagem (público) — com cache longo, pois a URL é única por imagem
app.get('/api/img/:id', async (req, res) => {
  try {
    const { rows } = await pool.query('SELECT mime, data FROM images WHERE id = $1', [String(req.params.id)]);
    if (!rows[0]) return res.status(404).end();
    res.set('Content-Type', rows[0].mime);
    res.set('Cache-Control', 'public, max-age=31536000, immutable');
    res.end(rows[0].data);
  } catch (e) {
    console.error('img', e);
    res.status(500).end();
  }
});

// Frontend (SPA de página única)
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'index.html'));
});

initDb()
  .then(() => {
    app.listen(PORT, () => console.log(`NX Digital rodando na porta ${PORT}`));
  })
  .catch((e) => {
    console.error('Falha ao iniciar o banco:', e);
    process.exit(1);
  });
