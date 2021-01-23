import random
import threading
import time
from queue import Queue
from typing import Dict, List

from selenium.common.exceptions import NoSuchElementException

from environment import TRACKED_USER_PERIOD, USER_SPIDER_PERIOD, MAX_UID
from spider import Spider
from tools import DBTool

import contextlib


class NoUserError(Exception):
    def __init__(self, uid):
        self.uid = uid

    def __str__(self):
        return repr(self.uid)


class UserSave(DBTool):
    col = DBTool.db["user_info"]
    col_lock = threading.Lock()

    def __init__(self, queue):
        DBTool.__init__(self, queue)

    def work(self) -> None:
        with self.col_lock:
            while not self.queue.empty():
                data = self.queue.get()
                query = {"uid": data["uid"]}
                old_data = self.col.find_one(query)
                if old_data is None:
                    self.col.insert_one(data)
                else:
                    new_states: List = old_data["states"]
                    new_states.append(data["states"][0])
                    new_values = {"$set": {"states": new_states}}
                    self.col.update_one(query, new_values)


class UserGet(DBTool):
    col = DBTool.db["user_rank"]

    def __init__(self, queue):
        DBTool.__init__(self, queue)

    def work(self) -> None:
        req: List = self.col.find()
        for user in req:
            uid: int = user["uid"]
            self.queue.put(uid)

        time.sleep(TRACKED_USER_PERIOD)


class UserSpider(Spider):
    data_queue = Queue()

    def __init__(self):
        Spider.__init__(self)
        self.tracked_users: Queue = Queue()

        UserSave(self.data_queue).start()
        UserGet(self.tracked_users).start()

    def __fetch_demand(self) -> int:
        if not self.tracked_users.empty():
            return self.tracked_users.get()
        else:
            return random.randint(1, MAX_UID)

    def __fetch_data(self, uid: int) -> Dict:
        def get_sex(sex) -> int:
            if sex == "icon gender male":
                return 1
            if sex == "icon gender female":
                return 2
            else:
                return 0

        def get_num(s: str) -> int:
            ans = 0
            nums = list(filter(str.isdigit, s))
            for c in nums:
                ans *= 10
                ans += int(c)
            return ans

        self.driver.get("https://space.bilibili.com/" + str(uid))

        # 判断账户是否注销
        try:
            self.driver.implicitly_wait(0)
            self.driver.find_element_by_class_name("error-container")
        except NoSuchElementException:
            pass
        else:
            raise NoUserError(uid)

        follow_xpath = "/html/body/div[@id='app']/div[@id='navigator']/div[@class='wrapper']/div[@class='n-inner clearfix']/div[@class='n-statistics']/a[@class='n-data n-gz']"
        fans_xpath = "/html/body/div[@id='app']/div[@id='navigator']/div[@class='wrapper']/div[@class='n-inner clearfix']/div[@class='n-statistics']/a[@class='n-data n-fs']"
        like_xpath = "/html/body/div[@id='app']/div[@id='navigator']/div[@class='wrapper']/div[@class='n-inner clearfix']/div[@class='n-statistics']/div[@class='n-data n-bf'][1]"
        view_xpath = "/html/body/div[@id='app']/div[@id='navigator']/div[@class='wrapper']/div[@class='n-inner clearfix']/div[@class='n-statistics']/div[@class='n-data n-bf'][2]"
        read_xpath = "/html/body/div[@id='app']/div[@id='navigator']/div[@class='wrapper']/div[@class='n-inner clearfix']/div[@class='n-statistics']/div[@class='n-data n-bf'][3]"
        state: Dict = {
            "follow": get_num(self.driver.find_element_by_xpath(follow_xpath).get_attribute("title")),
            "fans": get_num(self.driver.find_element_by_xpath(fans_xpath).get_attribute("title")),
            "like": get_num(self.driver.find_element_by_xpath(like_xpath).get_attribute("title")),
            "view": get_num(self.driver.find_element_by_xpath(view_xpath).get_attribute("title")),
            "read": get_num(self.driver.find_element_by_xpath(read_xpath).get_attribute("title")),
            "time": time.time()
        }
        states: List[Dict] = [state]

        name_xpath = "/html/body/div[@id='app']/div[@class='h']/div[@class='wrapper']/div[@class='h-inner']/div[@class='h-user']/div[@class='h-info clearfix']/div[@class='h-basic']/div[1]/span[@id='h-name']"
        sex_xpath = "/html/body/div[@id='app']/div[@class='h']/div[@class='wrapper']/div[@class='h-inner']/div[@class='h-user']/div[@class='h-info clearfix']/div[@class='h-basic']/div[1]/span[@id='h-gender']"
        face_xpath = "/html/body/div[@id='app']/div[@class='h']/div[@class='wrapper']/div[@class='h-inner']/div[@class='h-user']/div[@class='h-info clearfix']/div[@class='h-avatar']/img[@id='h-avatar']"
        sign_xpath = "/html/body/div[@id='app']/div[@class='h']/div[@class='wrapper']/div[@class='h-inner']/div[@class='h-user']/div[@class='h-info clearfix']/div[@class='h-basic']/div[@class='h-basic-spacing']/h4"
        level_xpath = "/html/body/div[@id='app']/div[@class='h']/div[@class='wrapper']/div[@class='h-inner']/div[@class='h-user']/div[@class='h-info clearfix']/div[@class='h-basic']/div[1]/a[@class='h-level m-level']"

        user_info: Dict = {
            "uid": uid,
            "name": self.driver.find_element_by_xpath(name_xpath).text,
            "sex": get_sex(self.driver.find_element_by_xpath(sex_xpath).get_attribute("class")),
            "face": self.driver.find_element_by_xpath(face_xpath).get_attribute("src"),
            "sign": self.driver.find_element_by_xpath(sign_xpath).get_attribute("title"),
            "level": int(self.driver.find_element_by_xpath(level_xpath).get_attribute("lvl")),
            "states": states
        }
        return user_info

    def run(self):
        print("user spider start")
        self.login()
        while True:
            uid: int = self.__fetch_demand()
            with contextlib.suppress(Exception):
                data: Dict = self.__fetch_data(uid)
                self.data_queue.put(data)
            time.sleep(USER_SPIDER_PERIOD)


if __name__ == '__main__':
    spider = UserSpider()
    spider.start()
