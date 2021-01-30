import contextlib
import json
import random
import threading
import time
from queue import Queue
from typing import Dict, List

from environment import MAX_AID, VIDEO_SPIDER_PERIOD, TRACKED_VIDEO_PERIOD
from spider import Spider
from tools import DBTool


class NoVideoError(Exception):
    def __init__(self, vid: str):
        self.vid = vid

    def __str__(self):
        return repr(self.vid)


class VideoSave(DBTool):
    col = DBTool.db["video_info"]
    col_lock = threading.Lock()

    def __init__(self, queue):
        DBTool.__init__(self, queue)

    def work(self) -> None:
        if self.queue.empty():
            return

        with self.col_lock:
            while not self.queue.empty():
                data = self.queue.get()
                query = {"aid": data["aid"]}
                old_data = self.col.find_one(query)
                if old_data is None:
                    self.col.insert_one(data)
                else:
                    new_states: List = old_data["states"]
                    new_states.append(data["states"][0])
                    new_values = {"$set": {"states": new_states}}
                    self.col.update_one(query, new_values)


class VideoGet(DBTool):
    col = DBTool.db["video_following"]

    def __init__(self, queue):
        DBTool.__init__(self, queue)

    def work(self) -> None:
        req: List = self.col.find()
        for user in req:
            bid: str = user["bid"]
            self.queue.put(bid)

        time.sleep(TRACKED_VIDEO_PERIOD)


class VideoSpider(Spider):
    data_queue = Queue()
    tracked_videos = Queue()
    videoSave = VideoSave(data_queue)
    videoGet = VideoGet(tracked_videos)

    def __init__(self):
        Spider.__init__(self)
        self.tracked_videos: Queue = Queue()
        if not self.videoSave.is_alive():
            self.videoSave.start()
        if not self.videoGet.is_alive():
            self.videoGet.start()

    def __fetch_demand(self) -> str:
        if not self.tracked_videos.empty():
            return self.tracked_videos.get()
        else:
            return str(random.randint(1, MAX_AID))

    def __fetch_data(self, vid: str) -> Dict:
        if vid[0] == 'B':  # bid是以BV开头的
            self.driver.get("http://api.bilibili.com/x/web-interface/view?bvid=" + vid)
        else:
            self.driver.get("http://api.bilibili.com/x/web-interface/view?aid=" + vid)
        req: Dict = json.loads(self.driver.find_element_by_xpath("/html/body/pre").text)

        if req["code"] != 0:
            raise NoVideoError(vid)

        data_sub_keys = [
            "aid", "bid", "cid", "tid",
            "title", "desc", "pic",
            "copyright", "pubdate", "duration",
            "owner", "dimension"
        ]
        video_info = {}
        for key in data_sub_keys:
            if key == "bid":
                video_info[key] = req["data"]["bvid"]
                continue
            video_info[key] = req["data"][key]

        state: Dict = {}
        state_sub_keys = [
            "view", "danmaku", "reply", "favorite", "coin", "share", "like"
        ]
        for key in state_sub_keys:
            state[key] = req["data"]["stat"][key]
        state["time"] = time.time()

        video_info["states"] = [state]
        return video_info

    def run(self):
        print("video spider start")
        # self.login()
        while True:
            # vid可以是aid也可以是bid
            vid: str = self.__fetch_demand()
            with contextlib.suppress(Exception):
                data: Dict = self.__fetch_data(vid)
                self.data_queue.put(data)
            time.sleep(VIDEO_SPIDER_PERIOD)


if __name__ == '__main__':
    spider = VideoSpider()
    spider.start()
