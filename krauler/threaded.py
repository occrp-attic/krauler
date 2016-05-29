from krauler.crawler import Krauler
from threading import Thread
from krauler.signals import on_wait


class ThreadedKrauler(Krauler):

    def process_queue(self):
        while True:
            self.process_next()

    def run(self):
        self.init()

        for i in range(self.config.threads):
            t = Thread(target=self.process_queue)
            t.daemon = True
            t.start()

        on_wait.send(self)
        self.queue.join()
