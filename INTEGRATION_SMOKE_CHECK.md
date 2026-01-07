# Integration Smoke Check (Frontend 3000 → Backend 3001 → SQLite)

This repo is split across three containers:

- `notes_frontend` (React) on port **3000**
- `notes_backend` (FastAPI) on port **3001**
- `database` (SQLite file) in `simple-notes-app-195720-195731/database/myapp.db`

## What “good” looks like

- `GET http://localhost:3001/` returns `{"message":"Healthy"}`
- `GET http://localhost:3001/notes` returns a JSON array with seeded notes (e.g. "Welcome", "Tips")
- Create/Edit/Delete notes from the frontend persist to the SQLite DB file
- No 4xx/5xx responses for normal CRUD operations
- CORS allows `http://localhost:3000`

## Quick CLI verification (backend must be running)

List notes:

```bash
python -c "import urllib.request, json; print(json.loads(urllib.request.urlopen('http://localhost:3001/notes').read())[:2])"
```

Create/update/delete:

```bash
python - <<'PY'
import urllib.request, json
base='http://localhost:3001'
payload=json.dumps({'title':'Smoke Test','content':'hello'}).encode()
req=urllib.request.Request(base+'/notes',data=payload,headers={'Content-Type':'application/json','Accept':'application/json'},method='POST')
created=json.loads(urllib.request.urlopen(req).read())
print('created',created)

nid=created['id']
payload=json.dumps({'content':'updated'}).encode()
req=urllib.request.Request(base+f'/notes/{nid}',data=payload,headers={'Content-Type':'application/json','Accept':'application/json'},method='PUT')
print('updated',json.loads(urllib.request.urlopen(req).read()))

req=urllib.request.Request(base+f'/notes/{nid}',headers={'Accept':'application/json'},method='DELETE')
resp=urllib.request.urlopen(req)
print('delete_status',resp.status)
PY
```

Verify SQLite has seeded notes (database file must exist):

```bash
python -c "import sqlite3; db='simple-notes-app-195720-195731/database/myapp.db'; conn=sqlite3.connect(db); print(conn.execute('select id,title from notes order by id').fetchall()); conn.close()"
```
