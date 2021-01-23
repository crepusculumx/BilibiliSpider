import contextlib
import threading
import threading
import time
from queue import Queue
from typing import Dict, List

from environment import USER_SPIDER_PERIOD, TRACKED_VIDEO_PERIOD
from spider import Spider
from tools import DBTool


class VideoFollowingSave(DBTool):
    col = DBTool.db["video_following"]
    col_lock = threading.Lock()

    def __init__(self, queue):
        DBTool.__init__(self, queue)

    def work(self) -> None:
        if self.queue.empty():
            return

        with self.col_lock:
            while not self.queue.empty():
                data = self.queue.get()
                query = {"bid": data["bid"]}
                if self.col.find_one(query) is None:
                    self.col.insert_one(data)


class VideoFollowingGet(DBTool):
    col = DBTool.db["user_rank"]

    def __init__(self, queue):
        DBTool.__init__(self, queue)

    def work(self) -> None:
        while True:
            req: List = self.col.find()
            for user in req:
                uid: int = user["uid"]
                self.queue.put(uid)

            time.sleep(TRACKED_VIDEO_PERIOD)


class VideoFollowingSpider(Spider):
    data_queue = Queue()

    def __init__(self):
        Spider.__init__(self)
        self.tracked_users: Queue = Queue()

        VideoFollowingSave(self.data_queue).start()
        VideoFollowingGet(self.tracked_users).start()

    def __fetch_demand(self) -> int:
        while True:
            if not self.tracked_users.empty():
                return self.tracked_users.get()
            time.sleep(5)

    def __fetch_data(self, uid: int) -> Dict:
        self.driver.get("https://space.bilibili.com/" + str(uid) + "/video")
        xpath = "/html/body/div[@id='app']/div[@class='s-space']/div/div[@id='page-video']/div[@class='col-full clearfix']/div[@class='main-content']/div[@id='submit-video']/div[@id='video-list-style']/div[@id='submit-video-list']/ul[@class='clearfix cube-list']/li[@class='small-item fakeDanmu-item'][1]"
        bid: str = self.driver.find_element_by_xpath(xpath).get_attribute("data-aid")
        return {"bid": bid}

    def run(self):
        print("video following spider start")
        self.login()
        while True:
            uid: int = self.__fetch_demand()
            with contextlib.suppress(Exception):
                data: Dict = self.__fetch_data(uid)
                self.data_queue.put(data)
            time.sleep(USER_SPIDER_PERIOD)


if __name__ == '__main__':
    spider = VideoFollowingSpider()
    spider.start()
