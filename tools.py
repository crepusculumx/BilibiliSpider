import time
from queue import Queue
from threading import Thread
from typing import List

import environment


class DBTool(Thread):
    db = environment.DB

    def __init__(self, queue: Queue, period: int = 5):
        Thread.__init__(self)
        self.queue = queue
        self.period = period

    def work(self) -> None:
        # 子类重写work
        return

    def run(self) -> None:
        while True:
            self.work()
            time.sleep(self.period)


class DelaySave(Thread):
    # 延时delay_time将data数组中元素添加到queue中
    def __init__(self, queue: Queue, delay_time: int, data: List):
        Thread.__init__(self)
        self.queue = queue
        self.delay_time = delay_time
        self.data = data

    def run(self) -> None:
        time.sleep(self.delay_time)
        for data in self.data:
            self.queue.put(data)
