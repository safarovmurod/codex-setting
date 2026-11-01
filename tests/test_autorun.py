import json
from pathlib import Path
import sys
import tempfile
import threading
import unittest
import uuid

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from codex_setting.autorun import Controller

T=str(uuid.uuid4()); OTHER=str(uuid.uuid4()); TURN=str(uuid.uuid4())

class Source:
    def __init__(self):
        self.row={'thread_id':T,'turn_id':TURN,'status':'inProgress','category':None,'ordinal':3,'completed_at':900}
        self.eligible=True;self.fresh=True;self.queued=0;self.later=[];self.hint={'reset_at':950,'uncertain':False}
    def taken(self,thread,kinds):return self.eligible and thread==T
    def latest(self,thread):return dict(self.row)
    def projection(self,thread):return {'fresh':self.fresh}
    def foreign_queued(self,*args):return self.queued
    def queued_rows(self,*args):return []
    def later_turns(self,thread,checkpoint,marker):return [r for r in self.later if r.get('ordinal',checkpoint+1)>checkpoint]
    def reset_hint(self,*args):return self.hint
    def queue_row(self,*args):return {'exists':True,'has_marker':True}

class Backend:
    def __init__(self):self.sends=[];self.deletes=[];self.probes=0;self.available=True;self.outcome='accepted'
    def usage(self):self.probes+=1;return {'available':self.available,'reset_at':1100 if not self.available else None}
    def send(self,thread,prompt,launch_guard):
        with launch_guard as allowed:
            if not allowed:return {'outcome':'not_started'}
            self.sends.append((thread,prompt))
        return {'outcome':self.outcome,'queue_id':str(uuid.uuid4()) if self.outcome=='accepted' else None}
    def delete_queue(self,thread,queue):self.deletes.append((thread,queue));return True

class Runtime:
    def __init__(self):self.source=Source();self.backend=Backend();self.loaded=True
    def ready(self,thread):return self.loaded

class AutorunTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);self.runtime=Runtime()
        self.now=1000;self.c=Controller(self.root,'host-A',self.runtime,lambda:self.now)
    def tearDown(self):self.temp.cleanup()
    def arm(self):return self.c.arm(T,'Implement the authorized task',True)
    def fail(self):self.runtime.source.row.update(status='failed',category='usage_limit')
    def test_no_implicit_activation(self):
        with self.assertRaises(ValueError):self.c.arm(T,'task',False)
        self.c.tick();self.assertEqual(self.runtime.backend.probes,0)
    def test_no_task_no_activation(self):
        with self.assertRaises(ValueError):self.c.arm(T,' ',True)
    def test_subagent_or_other_thread_is_rejected(self):
        with self.assertRaises(ValueError):self.c.arm(OTHER,'task',True)
    def test_same_turn_activation_is_idempotent(self):self.assertEqual(self.arm()['task'],self.arm()['task'])
    def test_new_turn_gets_new_task_generation(self):
        first=self.arm()['task'];self.runtime.source.row['ordinal']=4
        self.assertNotEqual(first,self.arm()['task'])
    def test_only_armed_thread_can_send(self):
        self.arm();self.fail();self.c.tick()
        self.assertEqual(len(self.runtime.backend.sends),1);self.assertEqual(self.runtime.backend.sends[0][0],T)
    def test_second_tick_and_restart_do_not_resend(self):
        self.arm();self.fail();self.c.tick();self.c.tick()
        Controller(self.root,'host-A',self.runtime,lambda:self.now).tick()
        self.assertEqual(len(self.runtime.backend.sends),1)
    def test_host_isolation(self):
        self.arm();self.fail();Controller(self.root,'host-B',self.runtime).tick()
        self.assertFalse(self.runtime.backend.sends)
    def test_uncertain_send_never_retries(self):
        self.arm();self.fail();self.runtime.backend.outcome='unknown';self.c.tick();self.c.tick()
        self.assertEqual(len(self.runtime.backend.sends),1)
    def test_crash_after_claim_does_not_resend(self):
        task=self.arm();self.fail();self.c.store.claim(task,TURN);self.c.tick()
        self.assertFalse(self.runtime.backend.sends)
    def test_multiple_watchers_dispatch_once(self):
        self.arm();self.fail()
        other=Controller(self.root,'host-A',self.runtime,lambda:self.now)
        threads=[threading.Thread(target=c.tick) for c in (self.c,other)]
        for t in threads:t.start()
        for t in threads:t.join()
        self.assertEqual(len(self.runtime.backend.sends),1)
    def test_blocked_quota_waits_for_fresh_read(self):
        self.arm();self.fail();self.runtime.backend.available=False;self.c.tick()
        self.assertFalse(self.runtime.backend.sends)
        self.runtime.backend.available=True;self.c.tick();self.assertFalse(self.runtime.backend.sends)
        self.now=1101;self.c.tick();self.assertEqual(len(self.runtime.backend.sends),1)
    def test_future_reset_not_just_available_bucket(self):
        self.arm();self.fail();self.runtime.source.hint={'reset_at':1200,'uncertain':False};self.c.tick()
        self.assertFalse(self.runtime.backend.sends)
    def test_unknown_quota_never_sends(self):
        self.arm();self.fail();self.runtime.backend.available=None;self.c.tick()
        self.assertFalse(self.runtime.backend.sends)
    def test_missing_reset_and_no_observed_block_is_not_proof(self):
        self.arm();self.fail();self.runtime.source.hint={'reset_at':None,'uncertain':True};self.c.tick()
        self.assertFalse(self.runtime.backend.sends)
    def test_uncertain_timestamp_is_not_proof(self):
        self.arm();self.fail();self.runtime.source.hint={'reset_at':950,'uncertain':True};self.c.tick()
        self.assertFalse(self.runtime.backend.sends)
    def test_stale_projection_or_unloaded_thread_never_sends(self):
        self.arm();self.fail();self.runtime.source.fresh=False;self.c.tick()
        self.runtime.source.fresh=True;self.runtime.loaded=False;self.c.tick()
        self.assertFalse(self.runtime.backend.sends)
    def test_queued_message_blocks(self):
        self.arm();self.fail();self.runtime.source.queued=1;self.c.tick();self.assertFalse(self.runtime.backend.sends)
    def test_human_followup_requires_rearm(self):
        self.arm();self.fail();self.runtime.source.later=[{'kind':'foreign'}];self.c.tick()
        self.assertEqual(self.c.store.task('host-A',T)['status'],'paused');self.assertFalse(self.runtime.backend.sends)
    def test_native_stop_disarms(self):
        self.arm();self.runtime.source.row['status']='interrupted';self.c.tick()
        self.assertEqual(self.c.store.task('host-A',T)['status'],'paused')
    def test_off_removes_owned_accepted_queue_and_stops(self):
        self.arm();self.fail();self.c.tick();self.c.off(T)
        self.assertEqual(len(self.runtime.backend.deletes),1)
        self.runtime.source.row['turn_id']=str(uuid.uuid4());self.c.tick();self.assertEqual(len(self.runtime.backend.sends),1)
    def test_non_quota_failure_is_not_retried(self):
        self.arm();self.fail();self.runtime.source.row['category']='network_transient';self.c.tick()
        self.assertFalse(self.runtime.backend.sends)
    def test_complete_requires_real_check_results_and_exact_task(self):
        task=self.arm()
        for evidence in ({'checks':[]},{'checks':[{'name':'build','exit_code':1}]}):
            with self.assertRaises(ValueError):self.c.complete(T,task['task'],evidence)
        with self.assertRaises(ValueError):self.c.complete(T,str(uuid.uuid4()),{'checks':[{'name':'build','exit_code':0}]})
        self.c.complete(T,task['task'],{'checks':[{'name':'build','exit_code':0}]});self.fail();self.c.tick()
        self.assertFalse(self.runtime.backend.sends)
    def test_normal_completed_turn_does_not_trigger_work(self):
        self.arm();self.runtime.source.row['status']='completed';self.c.tick()
        self.assertEqual(self.runtime.backend.probes,0);self.assertFalse(self.runtime.backend.sends)
    def test_off_works_without_runtime_and_cancellation_survives_restart(self):
        self.arm();self.fail();self.c.tick()
        offline=Controller(self.root,'host-A',None);offline.off(T)
        self.assertEqual(offline.store.task('host-A',T)['status'],'off')
        self.assertEqual(len(offline.store.pending_cancellations('host-A')),1)
        self.c.tick();self.assertEqual(len(self.runtime.backend.deletes),1)
        self.assertEqual(self.c.store.pending_cancellations('host-A'),[])
    def test_off_does_not_delete_owner_edited_queue_item(self):
        self.arm();self.fail();self.c.tick()
        self.runtime.source.queue_row=lambda *args:{'exists':True,'has_marker':False}
        self.c.off(T);self.assertFalse(self.runtime.backend.deletes)

    def next_human(self,status='inProgress'):
        row=self.runtime.source.row
        row.update(turn_id=str(uuid.uuid4()),ordinal=row['ordinal']+1,status=status,category='usage_limit' if status=='failed' else None)
        self.runtime.source.later=[dict(row,kind='foreign',reason='later_turn_exists')]

    def test_connect_without_task_is_idle_and_requires_explicit_consent(self):
        with self.assertRaises(ValueError):self.c.connect(T)
        self.c.connect(T,explicit=True);self.c.tick()
        self.assertIsNone(self.c.store.task('host-A',T));self.assertEqual(self.runtime.backend.probes,0)

    def test_connected_chat_adopts_normal_followup_and_recovers_once(self):
        self.c.connect(T,explicit=True);self.next_human('failed')
        self.c.tick();self.c.tick()
        self.assertEqual(len(self.runtime.backend.sends),1)
        self.assertEqual(self.c.store.task('host-A',T)['checkpoint'],'4')

    def test_connection_survives_completion_and_takes_next_task(self):
        self.c.connect(T,'first task',True);task=self.c.store.task('host-A',T)
        self.c.complete(T,task['task'],{'checks':[{'name':'check','exit_code':0}]})
        self.next_human();self.c.tick()
        self.assertNotEqual(self.c.store.task('host-A',T)['task'],task['task'])
        self.assertEqual(self.c.store.task('host-A',T)['status'],'armed')
        self.assertFalse(self.runtime.backend.sends)

    def test_connected_native_stop_stays_stopped_until_new_human_task(self):
        self.c.connect(T,'task',True);self.runtime.source.row['status']='interrupted';self.c.tick()
        self.c.tick();self.assertEqual(self.c.store.task('host-A',T)['status'],'paused')
        self.assertFalse(self.runtime.backend.sends)
        self.next_human();self.c.tick();self.assertEqual(self.c.store.task('host-A',T)['status'],'armed')

    def test_off_removes_persistent_consent_for_future_tasks(self):
        self.c.connect(T,'task',True);self.c.off(T);self.next_human('failed');self.c.tick()
        self.assertFalse(self.c.store.connections('host-A'));self.assertFalse(self.runtime.backend.sends)

    def test_persistent_consent_survives_restart_but_not_other_host(self):
        self.c.connect(T,explicit=True);self.next_human('failed')
        Controller(self.root,'host-B',self.runtime,lambda:self.now).tick()
        self.assertFalse(self.runtime.backend.sends)
        Controller(self.root,'host-A',self.runtime,lambda:self.now).tick()
        self.assertEqual(len(self.runtime.backend.sends),1)

    def test_missing_user_item_and_own_continuation_do_not_create_task(self):
        self.c.connect(T,explicit=True);self.next_human('failed')
        self.runtime.source.later[0]['reason']='turn_without_user_item';self.c.tick()
        self.assertIsNone(self.c.store.task('host-A',T))
        self.runtime.source.later[0].update(kind='ours',reason=None);self.c.tick()
        self.assertIsNone(self.c.store.task('host-A',T))

    def test_connected_stale_history_never_adopts(self):
        self.c.connect(T,explicit=True);self.next_human('failed');self.runtime.source.fresh=False
        self.c.tick();self.assertIsNone(self.c.store.task('host-A',T))

    def test_concurrent_connected_watchers_adopt_and_send_once(self):
        self.c.connect(T,explicit=True);self.next_human('failed')
        other=Controller(self.root,'host-A',self.runtime,lambda:self.now)
        workers=[threading.Thread(target=c.tick) for c in (self.c,other)]
        for worker in workers:worker.start()
        for worker in workers:worker.join()
        self.assertEqual(len(self.runtime.backend.sends),1)

if __name__=='__main__':unittest.main()
