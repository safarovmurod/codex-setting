from __future__ import annotations

from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import time
import uuid

from .common import file_lock, save_json
from .store import Store


def thread_id(value):
    parsed=str(uuid.UUID(value))
    if value!=parsed: raise ValueError('CANONICAL_THREAD_UUID_REQUIRED')
    return value


class Controller:
    def __init__(self,root,host,runtime,clock=time.time):
        self.root=Path(root);self.host=host;self.runtime=runtime;self.clock=clock
        self.store=Store(self.root)
        self.next_probe={}

    def lock(self,thread): return self.root/(thread+'.lock')
    def marker(self,task): return '[codex-auto-resume:'+hashlib.sha256(('codex-setting:'+task['task']).encode()).hexdigest()+']'

    def cancel_owned(self,row):
        if not self.runtime:return
        try:
            actual=self.runtime.source.queue_row(row['thread'],row['queue_id'],self.marker(row))
            if actual.get('exists') and actual.get('has_marker'):
                if self.runtime.backend.delete_queue(row['thread'],row['queue_id']) is not True:return
            self.store.cancelled(row)
        except Exception:pass  # Persistent cancellation is reconciled after the host returns.

    def arm(self,thread,goal,explicit=False):
        thread_id(thread)
        if not explicit or not goal.strip(): raise ValueError('EXPLICIT_AUTORUN_AND_TASK_REQUIRED')
        if len(goal)>16000: raise ValueError('TASK_TOO_LONG')
        if not self.runtime.source.taken(thread,frozenset()): raise ValueError('NOT_AN_OWNER_DESKTOP_THREAD')
        latest=self.runtime.source.latest(thread)
        if not latest or latest['status']!='inProgress': raise ValueError('ARM_FROM_THE_CURRENT_ACTIVE_TURN')
        with file_lock(self.lock(thread)):
            task=self.store.arm(self.host,thread,hashlib.sha256(goal.encode()).hexdigest(),str(latest['ordinal']))
        return task

    def off(self,thread):
        thread_id(thread)
        with file_lock(self.lock(thread),timeout=60):
            self.store.stop(self.host,thread)
            # Remove only our positively acknowledged queue items, never somebody else's.
            for row in self.store.attempts(self.host,thread):
                if row['queue_id']:self.cancel_owned(row)
        pending=[r for r in self.store.pending_cancellations(self.host) if r['thread']==thread]
        return {'status':'off','thread':thread,'owned_queue_cancellations_pending':len(pending)}

    def complete(self,thread,task,evidence):
        checks=evidence.get('checks') if isinstance(evidence,dict) else None
        if not checks or not all(isinstance(c,dict) and c.get('name') and type(c.get('exit_code')) is int and c['exit_code']==0 for c in checks):
            raise ValueError('SUCCESSFUL_ACCEPTANCE_CHECKS_REQUIRED')
        with file_lock(self.lock(thread)):
            row=self.store.task(self.host,thread)
            if not row or row['status']!='armed' or row['task']!=task: raise ValueError('WRONG_ACTIVE_TASK')
            self.store.stop(self.host,thread,'completed','acceptance_checks_completed')
            for attempt in self.store.attempts(self.host,thread):
                if attempt['queue_id']:self.cancel_owned(attempt)
        return {'status':'completed','task':task}

    def gate(self,task,turn):
        live=self.store.task(self.host,task['thread'])
        if not live or live['status']!='armed' or live['task']!=task['task']: return 'not_armed'
        source=self.runtime.source
        if not source.taken(task['thread'],frozenset()): return 'thread_ineligible'
        if source.projection(task['thread']).get('fresh') is not True: return 'history_not_fresh'
        latest=source.latest(task['thread'])
        if not latest or latest['turn_id']!=turn['turn_id'] or latest['ordinal']!=turn['ordinal']: return 'turn_changed'
        if latest['status']!='failed' or latest['category']!='usage_limit': return 'not_usage_limit'
        if not self.runtime.ready(task['thread']): return 'open_this_chat_on_host_or_remote'
        marker=self.marker(task)
        if source.foreign_queued(task['thread'],marker) or source.queued_rows(task['thread'],marker): return 'queue_not_empty'
        later=source.later_turns(task['thread'],int(task['checkpoint']),marker)
        if any(x.get('kind')=='foreign' for x in later): return 'new_user_turn_requires_rearm'
        if any(x.get('kind')=='undetermined' for x in later): return 'history_not_fresh'
        return None

    def tick_task(self,task):
        thread=task['thread'];source=self.runtime.source
        latest=source.latest(thread)
        if not latest: return 'history_unavailable'
        if latest['status'] in ('interrupted','cancelled','canceled'):
            self.store.stop(self.host,thread,'paused','user_stopped');return 'user_stopped'
        if latest['status']!='failed': return 'working_or_idle'
        if latest['category']!='usage_limit':
            self.store.stop(self.host,thread,'paused','non_quota_failure');return 'non_quota_failure'
        reason=self.gate(task,latest)
        if reason:
            if reason=='new_user_turn_requires_rearm': self.store.stop(self.host,thread,'paused',reason)
            return reason
        turn=latest['turn_id'];now=self.clock()
        if any(a['task']==task['task'] and a['turn']==turn for a in self.store.attempts(self.host,thread)):
            return 'already_claimed_no_resend'
        if now<self.next_probe.get(thread,0): return 'waiting_reset'
        hint=source.reset_hint(thread,turn)
        reset=hint.get('reset_at')
        if hint.get('uncertain') is True or type(reset) not in (float,int) or reset<latest['completed_at']: reset=None
        usage=self.runtime.backend.usage()
        wait=self.store.wait(self.host,thread,turn,reset=reset,blocked=usage.get('available') is False)
        if usage.get('available') is False:
            next_reset=usage.get('reset_at')
            self.next_probe[thread]=max(now+60,next_reset or 0)
            return 'quota_blocked'
        if usage.get('available') is not True:
            self.next_probe[thread]=now+60;return 'quota_unknown'
        if wait['reset'] and now<wait['reset']:
            self.next_probe[thread]=wait['reset'];return 'waiting_reset'
        if not wait['reset'] and not wait['blocked']: return 'quota_reset_not_proven'
        # Check again immediately before claim; never overwrite the task's model/settings.
        with file_lock(self.lock(thread),timeout=60):
            reason=self.gate(task,latest)
            if reason: return reason
            if not self.store.claim(task,turn): return 'already_claimed_no_resend'
            @contextmanager
            def launch_guard():
                yield self.gate(task,latest) is None
            prompt=(f'Шеф AUTORUN-ро барои ҳамин вазифа фаъол кардааст. Фақат кори боқимондаи ҳамин вазифаро давом деҳ. '
                    f'Аввал санҷ: агар тамом шуда бошад, кори нав насоз ва AUTORUN-ро complete кун. '
                    f'Модел ва иҷозатҳоро иваз накун. Баъди санҷиши натиҷа вазифаи {task["task"]}-ро complete кун. '
                    f'Агар соҳиби чат Stop/Pause/off дода бошад, давом надеҳ. {self.marker(task)}')
            try: result=self.runtime.backend.send(thread,prompt,launch_guard=launch_guard())
            except Exception: result={'outcome':'unknown'}
            self.store.receipt(task,turn,result)
        return result['outcome']

    def tick(self):
        result=[]
        for row in self.store.pending_cancellations(self.host):self.cancel_owned(row)
        for task in self.store.armed(self.host):
            try: reason=self.tick_task(task)
            except Exception: reason='runtime_unavailable'
            self.store.reason(self.host,task['thread'],reason)
            result.append({'thread':task['thread'],'reason':reason})
        return result
