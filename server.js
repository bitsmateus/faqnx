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
