import time
from queue import Queue

from environment import RANK_PERIOD
from spider import Spider
from tools import DBTool


class RankSave(DBTool):
    col = DBTool.db["user_rank"]

    def __init__(self, queue):
        DBTool.__init__(self, queue, RANK_PERIOD)

    def work(self) -> None:
        while not self.queue.empty():
            data = self.queue.get()
            query = {"rank": data["rank"]}
            old_data = self.col.find_one(query)
            if old_data is None:
                self.col.insert_one(data)
            else:
                new_uid: int = data["uid"]
                new_values = {"$set": {"uid": new_uid}}
                self.col.update_one(query, new_values)


class RankSpider(Spider):
    data_queue = Queue()
    rankSave = RankSave(data_queue)

    def __init__(self):
        Spider.__init__(self)
        if not self.rankSave.is_alive():
            self.rankSave.start()

    def run(self) -> None:
        def get_num(s: str) -> int:
            ans = 0
            nums = list(filter(str.isdigit, s))
            for c in nums:
                ans *= 10
                ans += int(c)
            return ans

        print("rank spider start")
        while True:
            self.driver.get("https://www.kanbilibili.com/rank/ups/fans")
            xpath = "/html/body/div[@id='app']/div[@class='rank-container relative']/div[@class='main-inner content fans']/div[@class='ups-list']/a"
            users = self.driver.find_elements_by_xpath(xpath)
            for i in range(len(users)):
                href = users[i].get_attribute("href")
                data = {
                    "rank": i + 1,
                    "uid": get_num(href)
                }
                self.data_queue.put(data)

            time.sleep(RANK_PERIOD)


if __name__ == '__main__':
    rankSpider = RankSpider()
    rankSpider.start()
