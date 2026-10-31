from __future__ import annotations

from contextlib import contextmanager
import json
from pathlib import Path
import sqlite3
import time
import uuid


class Store:
    """Own state only. Never writes Codex databases or stores conversation text."""
    def __init__(self, root: Path):
        self.root=root
        root.mkdir(parents=True,exist_ok=True)
        self.path=root/'autorun.sqlite'
        with self.db() as db:
            db.executescript('''
              CREATE TABLE IF NOT EXISTS tasks (
                host TEXT, thread TEXT, task TEXT, status TEXT, armed REAL,
                goal_hash TEXT, checkpoint TEXT, last_reason TEXT,
                PRIMARY KEY(host,thread));
              CREATE TABLE IF NOT EXISTS attempts (
                host TEXT, thread TEXT, task TEXT, turn TEXT, status TEXT,
                queue_id TEXT, at REAL, PRIMARY KEY(host,thread,task,turn));
              CREATE TABLE IF NOT EXISTS waits (
                host TEXT, thread TEXT, turn TEXT, reset REAL, blocked INTEGER,
                PRIMARY KEY(host,thread,turn));
            ''')

    @contextmanager
    def db(self):
        db=sqlite3.connect(self.path,timeout=10)
        try:
            db.row_factory=sqlite3.Row
            db.execute('PRAGMA busy_timeout=10000')
            with db:yield db
        finally:
            db.close()

    def arm(self,host,thread,goal_hash,checkpoint):
        with self.db() as db:
            db.execute('BEGIN IMMEDIATE')
            old=db.execute('SELECT * FROM tasks WHERE host=? AND thread=?',(host,thread)).fetchone()
            if old and old['status']=='armed' and old['goal_hash']==goal_hash and old['checkpoint']==checkpoint: return dict(old)
            task=str(uuid.uuid4())
            db.execute('INSERT OR REPLACE INTO tasks VALUES (?,?,?,?,?,?,?,?)',
                       (host,thread,task,'armed',time.time(),goal_hash,checkpoint,'explicit_invocation'))
            return dict(db.execute('SELECT * FROM tasks WHERE host=? AND thread=?',(host,thread)).fetchone())

    def task(self,host,thread):
        with self.db() as db:
            row=db.execute('SELECT * FROM tasks WHERE host=? AND thread=?',(host,thread)).fetchone()
            return dict(row) if row else None

    def armed(self,host):
        with self.db() as db:
            return [dict(r) for r in db.execute('SELECT * FROM tasks WHERE host=? AND status=?',(host,'armed'))]

    def stop(self,host,thread,status='off',reason='explicit_off'):
        with self.db() as db:
            db.execute('UPDATE tasks SET status=?,last_reason=? WHERE host=? AND thread=?',(status,reason,host,thread))

    def reason(self,host,thread,reason):
        with self.db() as db:
            db.execute('UPDATE tasks SET last_reason=? WHERE host=? AND thread=?',(reason,host,thread))

    def claim(self,task,turn):
        with self.db() as db:
            db.execute('BEGIN IMMEDIATE')
            live=db.execute('SELECT status,task FROM tasks WHERE host=? AND thread=?',(task['host'],task['thread'])).fetchone()
            if not live or live['status']!='armed' or live['task']!=task['task']: return False
            try:
                db.execute('INSERT INTO attempts VALUES (?,?,?,?,?,?,?)',
                    (task['host'],task['thread'],task['task'],turn,'claimed',None,time.time()))
            except sqlite3.IntegrityError: return False
            return True

    def receipt(self,task,turn,result):
        with self.db() as db:
            db.execute('UPDATE attempts SET status=?,queue_id=? WHERE host=? AND thread=? AND task=? AND turn=?',
                (result['outcome'],result.get('queue_id'),task['host'],task['thread'],task['task'],turn))

    def attempts(self,host,thread):
        with self.db() as db:
            return [dict(x) for x in db.execute('SELECT * FROM attempts WHERE host=? AND thread=?',(host,thread))]

    def wait(self,host,thread,turn,reset=None,blocked=False):
        with self.db() as db:
            old=db.execute('SELECT * FROM waits WHERE host=? AND thread=? AND turn=?',(host,thread,turn)).fetchone()
            value={'reset':reset or (old['reset'] if old else None),'blocked':bool(blocked or (old['blocked'] if old else False))}
            db.execute('INSERT OR REPLACE INTO waits VALUES (?,?,?,?,?)',(host,thread,turn,value['reset'],value['blocked']))
            return value

    def pending_cancellations(self,host):
        with self.db() as db:
            return [dict(x) for x in db.execute('''SELECT a.* FROM attempts a JOIN tasks t
                ON a.host=t.host AND a.thread=t.thread
                WHERE a.host=? AND a.status='accepted' AND a.queue_id IS NOT NULL
                AND (t.status!='armed' OR t.task!=a.task)''',(host,))]

    def cancelled(self,row):
        with self.db() as db:
            db.execute("UPDATE attempts SET status='cancelled' WHERE host=? AND thread=? AND task=? AND turn=?",
                       (row['host'],row['thread'],row['task'],row['turn']))
