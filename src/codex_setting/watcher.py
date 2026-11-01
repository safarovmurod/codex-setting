"""Stay alive across host startup/update; idle polling never starts a model or probes quota."""
import time
from .common import save_json
from .store import Store
from .autorun import Controller


class Watcher:
    def __init__(self,root,host,runtime_factory):
        self.root=root;self.host=host;self.runtime_factory=runtime_factory
        self.store=Store(root/'state');self.controller=None

    def tick(self):
        armed=self.store.armed(self.host)
        pending=self.store.pending_cancellations(self.host)
        connections=self.store.connections(self.host)
        result={'status':'idle','armed':len(armed),'connected':len(connections),'pending_cancellations':len(pending),'checked_at':time.time()}
        if armed or pending or connections:
            try:
                if self.controller is None:self.controller=Controller(self.root/'state',self.host,self.runtime_factory())
                result.update(status='watching',tasks=self.controller.tick())
            except Exception:
                self.controller=None
                result['status']='waiting_for_host_runtime'
        save_json(self.root/'watcher-status.json',result)
        return result
