const GH_OWNER    = 'Abdulhadi446';
const GH_REPO     = 'spotify-clone';
const GH_WORKFLOW = 'add-song.yml';
const GH_BRANCH   = 'master';
const RAW_BASE    = `https://raw.githubusercontent.com/${GH_OWNER}/${GH_REPO}/${GH_BRANCH}`;
const GH_API_BASE = `https://api.github.com/repos/${GH_OWNER}/${GH_REPO}`;

let songsCache = null;
let songsCacheTime = 0;
const CACHE_TTL = 30_000;

export async function onRequest(context) {
  const { request, env } = context;
  const url = new URL(request.url);
  const path = url.pathname;

  try {
    switch (path) {
      case '/playlists':
        return json(await getSongs());
      case '/folders':
        return json(await getFolders());
      case '/download':
        if (request.method !== 'POST') return json({ error: 'Use POST' }, 405);
        return handleDownload(request, env);
      case '/create-playlist':
        if (request.method !== 'POST') return json({ error: 'Use POST' }, 405);
        return handleCreatePlaylist(request, env);
      case '/job':
        return handleJob(url, env);
      default:
        return json({ error: 'Not found' }, 404);
    }
  } catch (err) {
    return json({ error: err.message }, 500);
  }
}

async function getSongs() {
  const now = Date.now();
  if (songsCache && now - songsCacheTime < CACHE_TTL) return songsCache;
  const res = await fetch(`${RAW_BASE}/songs.json`);
  if (!res.ok) throw new Error(`Failed to fetch songs.json (${res.status})`);
  songsCache = await res.json();
  songsCacheTime = now;
  return songsCache;
}

async function getFolders() {
  const data = await getSongs();
  const folders = Object.keys(data).filter(k => k !== 'All Songs');
  return ['All Songs', ...folders];
}

function getToken(env) {
  const t = env?.GH_TOKEN;
  if (!t || t === 'YOUR_TOKEN_HERE') return null;
  return t;
}

async function ghFetch(path, token, opts = {}) {
  return fetch(`${GH_API_BASE}${path}`, {
    ...opts,
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: 'application/vnd.github+json',
      'User-Agent': 'spotify-clone-pages',
      'Content-Type': 'application/json',
      ...(opts.headers || {}),
    },
  });
}

async function handleDownload(request, env) {
  const tok = getToken(env);
  if (!tok) return json({ error: 'Server not configured (GH_TOKEN missing)' }, 500);

  let body;
  try { body = await request.json(); } catch {
    return json({ error: 'Invalid JSON body' }, 400);
  }

  const { url, folder } = body;
  if (!url || typeof url !== 'string') return json({ error: 'Missing field: url' }, 400);
  if (!url.startsWith('http://') && !url.startsWith('https://')) {
    return json({ error: 'Invalid URL format' }, 400);
  }

  const playlist = (folder || 'Downloads').replace(/[^a-zA-Z0-9_-]/g, '');
  if (!playlist || playlist.length > 64) return json({ error: 'Invalid playlist name' }, 400);

  const resp = await ghFetch(`/actions/workflows/${GH_WORKFLOW}/dispatches`, tok, {
    method: 'POST',
    body: JSON.stringify({ ref: GH_BRANCH, inputs: { url, playlist } }),
  });

  if (!resp.ok && resp.status !== 204) {
    const err = await resp.text();
    return json({ error: `GitHub API error (${resp.status}): ${err}` }, resp.status);
  }

  const runsRes = await ghFetch(
    `/actions/workflows/${GH_WORKFLOW}/runs?branch=${GH_BRANCH}&per_page=1&event=workflow_dispatch`,
    tok
  );
  let runId = null;
  if (runsRes.ok) {
    const runs = await runsRes.json();
    if (runs.workflow_runs?.length) runId = runs.workflow_runs[0].id;
  }

  return json({ ok: true, message: 'Download queued.', run_id: runId }, 202);
}

async function handleCreatePlaylist(request, env) {
  const tok = getToken(env);

  let body;
  try { body = await request.json(); } catch {
    return json({ error: 'Invalid JSON body' }, 400);
  }

  const name = (body.name || '').trim();
  if (!name || /[^a-zA-Z0-9 _-]/.test(name) || name.length > 64) {
    return json({ error: 'Invalid name' }, 400);
  }

  if (!tok) return json({ ok: true, folder: name, local: true });

  const filePath = `media/${name}/.gitkeep`;

  const refRes = await ghFetch(`/git/ref/heads/${GH_BRANCH}`, tok);
  if (!refRes.ok) return json({ error: 'Failed to get branch ref' }, 500);
  const ref = await refRes.json();

  const commitRes = await ghFetch(`/git/commits/${ref.object.sha}`, tok);
  if (!commitRes.ok) return json({ error: 'Failed to get commit' }, 500);
  const commit = await commitRes.json();

  const blobRes = await ghFetch('/git/blobs', tok, {
    method: 'POST',
    body: JSON.stringify({ content: '', encoding: 'utf-8' }),
  });
  if (!blobRes.ok) return json({ error: 'Failed to create blob' }, 500);
  const blob = await blobRes.json();

  const treeRes = await ghFetch('/git/trees', tok, {
    method: 'POST',
    body: JSON.stringify({
      base_tree: commit.tree.sha,
      tree: [{ path: filePath, mode: '100644', type: 'blob', sha: blob.sha }],
    }),
  });
  if (!treeRes.ok) return json({ error: 'Failed to create tree' }, 500);
  const tree = await treeRes.json();

  const newCommitRes = await ghFetch('/git/commits', tok, {
    method: 'POST',
    body: JSON.stringify({
      message: `Create playlist: ${name}`,
      tree: tree.sha,
      parents: [ref.object.sha],
    }),
  });
  if (!newCommitRes.ok) return json({ error: 'Failed to create commit' }, 500);
  const newCommit = await newCommitRes.json();

  await ghFetch(`/git/refs/heads/${GH_BRANCH}`, tok, {
    method: 'PATCH',
    body: JSON.stringify({ sha: newCommit.sha, force: false }),
  });

  songsCache = null;
  return json({ ok: true, folder: name });
}

async function handleJob(url, env) {
  const tok = getToken(env);
  const runId = url.searchParams.get('id');
  if (!runId || !tok) return json({ status: 'unknown' });

  const res = await ghFetch(`/actions/runs/${runId}`, tok);
  if (!res.ok) return json({ status: 'unknown' });

  const run = await res.json();
  const { status, conclusion } = run;

  if (status === 'completed') {
    if (conclusion === 'success') {
      songsCache = null;
      return json({ status: 'done', progress: 'Download complete!' });
    }
    return json({ status: 'error', error: `GitHub Actions: ${conclusion}` });
  }

  const progress = status === 'queued' ? 'Queued…' : 'Downloading…';
  return json({ status: 'running', progress });
}

function json(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      'Content-Type': 'application/json',
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
    },
  });
}
