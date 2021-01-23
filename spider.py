import threading

from selenium import webdriver

from environment import bilibili_accounts


class Spider(threading.Thread):
    __account_p = 0
    __account_p_lock = threading.Lock()

    def __init__(self):
        threading.Thread.__init__(self)
        self.driver = webdriver.Chrome()
        self.driver.implicitly_wait(15)

    def login(self) -> None:
        self.driver.get("https://passport.bilibili.com/login?gourl=https://space.bilibili.com")

        with self.__account_p_lock:
            if self.__account_p == bilibili_accounts:
                self.__account_p = 0
                print("b站账户不足以每个线程分配一个，将分配一个账户给多个线程")
            username = bilibili_accounts[self.__account_p]["username"]
            password = bilibili_accounts[self.__account_p]["password"]
            self.__account_p += 1
        self.driver.find_element_by_id("login-username").click()
        self.driver.find_element_by_id("login-username").send_keys(username)
        self.driver.find_element_by_id("login-passwd").click()
        self.driver.find_element_by_id("login-passwd").send_keys(password)
        input("登录后回车")
        return


if __name__ == '__main__':
    pass
