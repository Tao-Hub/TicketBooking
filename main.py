import re
import time
import base64
import requests
import sys
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# 发送邮件相关
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header


class Qiangpiao(object):
    #初始化函数
    def __init__(self, sw):
        self.login_url = "https://kyfw.12306.cn/otn/resources/login.html"
        self.initmy_url = 'https://kyfw.12306.cn/otn/view/index.html'
        self.search_url = 'https://kyfw.12306.cn/otn/leftTicket/init'
        self.confirmPassenger = 'https://kyfw.12306.cn/otn/confirmPassenger/initDc'

        self.sw = sw  # 浏览器运行的方式：0 后台运行 1 前台运行
        self.totalFlush = 0
        self.startTime = time.time()
        self.seat_list = {'商务座特等座': 'TZ_', '一等座': 'ZY_', '二等座': 'ZE_', 'GR_': '高级软卧', '软卧一等座': 'RW_', '动卧': 'SRRB_', '硬卧': 'YW_', '软座': 'RZ_', '硬座': 'YZ_', '无座': 'WZ_', '其他': 'QT_'}
        self.coordinate = [[-105, -20], [-35, -20], [40, -20], [110, -20], [-105, 50], [-35, 50], [40, 50], [110, 50]]

        # 第三方 SMTP 发送邮件服务
        self.mail_host = "smtp.163.com"  # SMTP服务器
        self.mail_user = "xxxxx@163.com"  # 用户名
        self.mail_password = "xxxxx"  # 授权密码，非登录密码
        self.sender = 'xxxxx'    # 发件人邮箱(最好写全, 不然会失败)
        self.receivers = ['xxxxx',]  # 接收邮件，可设置为你的QQ邮箱或者其他邮箱

        if self.sw == 0:
            print('运行无界面chromer')
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--disable-gpu')
            self.driver = webdriver.Chrome(chrome_options=chrome_options)
        else:
            # self.driver = '' #驱动chrome浏览器进行操作
            print('运行有界面chromer')
            driver = webdriver.Chrome()
            driver.set_window_size(1200, 900)
            self.driver = driver #驱动chrome浏览器进行操作

    def wait_input(self):
        # self.from_station = input('出发地：')
        # self.to_station = input('目的地：')
        # self.train_date = input('出发时间(格式：2019-01-01)：')
        # #名字一定要存在于常用联系人中间
        # self.train_numbers = input('车次(如有多个车次使用英文逗号分割)：').split(',') #结果[G234，...]
        # self.seat_types = input('座位类型(如[硬卧, 硬座])：').split(',')
        # self.passengers = input('乘客姓名：（如有多个乘客使用英文逗号分割）').split(',')

        self.from_station = '杭州'
        self.to_station = '武汉'
        self.train_date = "2019-02-02"
        self.train_numbers = ["D2246",]
        self.seat_types = ['二等座',]
        self.passengers = ['xxxxx',] # 乘客姓名


    def login_input(self):
        self.driver.get(self.login_url)
        time.sleep(0.2)
        try:
            WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.CLASS_NAME, 'login-hd-account')))
        except Exception as e:
            print(e)
        account = self.driver.find_element_by_class_name("login-hd-account")
        account.click()
        userName = self.driver.find_element_by_id("J-userName")
        userName.send_keys("xxxxx")  # 12306账号
        password = self.driver.find_element_by_id("J-password")
        password.send_keys("xxxxx")  # 12306密码


    def getVerifyImage(self):
        try:
            img_element = WebDriverWait(self.driver, 100).until( EC.presence_of_element_located((By.ID, "J-loginImg")))
        except Exception as e:
            print(u"网络开小差,请稍后尝试")
        base64_str = img_element.get_attribute("src").split(",")[-1]
        imgdata = base64.b64decode(base64_str)
        with open('verify.jpg', 'wb') as file:
            file.write(imgdata)
        self.img_element = img_element

    def getVerifyResult(self):
        url = "http://103.46.128.47:47720"  # 调用第三方图片识别接口
        files = {"pic_xxfile": ('verify.jpg', open('verify.jpg','rb'), 'image/jpeg')}
        response = requests.request("POST", url, data={"Content-Disposition": "form-data"}, files=files)
        result = []
        time.sleep(2)
        # print(response.text)
        # print(len(response.text))
        n = 0
        while len(response.text) <= 400: # error_len: 278
            response = requests.request("POST", url, data={"Content-Disposition": "form-data"}, files=files)
            print(response.text)
            n += 1
            if n > 5:
                break

        for i in re.findall("<B>(.*)</B>", response.text)[0].split(" "):
            result.append(int(i) - 1)
        self.result = result
        print('从左到右从上到下编号依次为:0 1 2 3 4 5 6 7, 经过仔细揣摩-图片貌似选择第{}个，正在尝试登录～'.format(result))

    def moveAndClick(self):
        try:
            Action = ActionChains(self.driver)
            for i in self.result:
                Action.move_to_element(self.img_element).move_by_offset(self.coordinate[i][0],
                                                                        self.coordinate[i][1]).click()
            Action.perform()
        except Exception as e:
            print(e)

    def submit(self):
        self.driver.find_element_by_id("J-login").click()

    def judge_login_status(self):
        try:
            WebDriverWait(self.driver, 4).until(EC.visibility_of_element_located((By.ID, 'J-header-logout')))
            user = self.driver.find_elements_by_xpath('//*[@id="J-header-logout"]/a[1]')[0].text
        except Exception as e:
            user = 0

        if user:
            if user == '登录':
                return 0
            else:
                return user
        else:
            return 0

    def run_login(self):
        # self._login()
        # self.wait_input()
        self.login_input()
        time.sleep(0.5)
        try:
            self.getVerifyImage()
            time.sleep(0.5)
            self.getVerifyResult()
            time.sleep(0.5)
            self.moveAndClick()
        except Exception as e:
            # 识别图片抛出异常，可能无需验证码
            print('图片识别异常')
            self.submit()
            time.sleep(0.5)
            # 判断登录是否成功
            return self.judge_login_status()

        time.sleep(0.1)
        self.submit()
        time.sleep(0.5)
        # 判断登录是否成功
        return self.judge_login_status()

    def login(self):
        status = self.run_login()
        if status == 0:
            print('登录失败，正在尝试重新登录！')
            status = self.run_login()
            if status != 0:
                print('登录成功，欢迎{}'.format(status))
                return
            elif status == 0 and self.sw == 0:
                print('2次尝试失败，请打开有界面浏览器手动识别图片！')
                self.driver.quit()
                sys.exit(0)
            else:
                print('2次尝试失败，请手动识别图片，8秒后将自动提交！')
                self.login_input()
                time.sleep(8)
                self.submit()
                # 判断登录是否成功
                status =  self.judge_login_status()
                if status == 0:
                    print('手动识别图片登录失败，请重试！')
                    self.driver.quit()
                    sys.exit(0)
                else:
                    print('登录成功，欢迎{}'.format(status))
        else:
            print('登录成功，欢迎{}'.format(status))

    def sendEmail(self, content):
        body_content = content
        subject = "抢票结果通知"
        message = MIMEText(body_content, 'plain', 'utf-8')
        message['Subject'] = Header(subject, 'utf-8')  # 邮件主题
        message['From'] = Header("抢票程序" + "<" + self.sender + ">", "utf-8")
        message['To'] = "<{}>".format(','.join(self.receivers))

        try:
            smtpObj = smtplib.SMTP_SSL('smtp.qq.com', 465)
            smtpObj.login(self.sender, self.mail_password)  # 登录验证
            smtpObj.sendmail(self.sender, self.receivers, message.as_string())  # 发送
            print("邮件发送成功！")
            smtpObj.quit()
        except smtplib.SMTPException as e:
            print('邮件发送失败！', e)

    def _order_ticket(self):
        # #1、跳转到查余票的界面
        self.driver.get(self.search_url)
        # self.driver.navigate().to(self.search_url)
        self.driver.find_element_by_id("fromStationText").click()
        self.driver.find_element_by_id("fromStationText").send_keys(self.from_station)
        o_InputSelect = self.driver.find_elements_by_class_name("ralign")  # 获取局部刷新的数据，然后循环比对文字
        for i in o_InputSelect:  # 注意：如果不用这种方法，用输入回车来选择会出现  要选北京结果选到北京西  这类的
            if i.text == self.from_station:
                i.click()
                break
        self.driver.find_element_by_id("toStationText").click()
        self.driver.find_element_by_id("toStationText").send_keys(self.to_station)
        o_InputSelect = self.driver.find_elements_by_class_name("ralign")  # 获取局部刷新的数据，然后循环比对文字
        for i in o_InputSelect:  # 注意：如果不用这种方法，用输入回车来选择会出现  要选北京结果选到北京西  这类的
            if i.text == self.to_station:
                i.click()
                break

        # 出发日
        year = self.train_date.split('-')[0]
        month = self.train_date.split('-')[1]
        day = self.train_date.split('-')[2]
        y = 4 if year == "2017" else 5 if year == "2018" else 6
        # m = int(month) - 1
        # d = int(day)-1
        m = int(month)
        d = int(day)
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.ID, 'date_icon_1'))).click()
        self.driver.find_element_by_xpath("//div[@class='year']/input").click()
        self.driver.find_element_by_xpath("//div[@class='year']/div/ul/li[%s]" % y).click()
        self.driver.find_element_by_xpath("//div[@class='month']/input").click()
        self.driver.find_element_by_xpath("//div[@class='month']/ul/li[%s]" % m).click()
        self.driver.find_element_by_xpath("//div[@class='cal']/div[@class='cal-cm']/div[%s]/div" % d).click()
        try:
            while True:
                try:
                    WebDriverWait(self.driver, 4).until(EC.element_to_be_clickable((By.ID, "query_ticket")))
                    time.sleep(0.05)
                    self.driver.find_element_by_id("query_ticket").click()
                    time.sleep(0.05)
                    WebDriverWait(self.driver, 4,).until(EC.presence_of_element_located((By.XPATH, ".//tbody[@id = 'queryLeftTable']/tr")))
                except Exception as e:
                    pass
                # 找到相应的火车信息datatrain属性的tr标签
                element = self.driver.find_elements_by_xpath(".//tbody[@id = 'queryLeftTable']/tr")
                if element:
                    for t in self.train_numbers:
                        current_tr = self.driver.find_elements_by_xpath('//*[@datatran="'+t+'"]')
                        current_ge = self.driver.find_elements_by_xpath('//*[@datatran="'+t+'"]/preceding-sibling::tr[1]')
                        current_id = current_tr[0].get_attribute("id").split('_')[1]

                        for i in self.seat_types:
                            id = self.seat_list[i]+current_id
                            current_td = self.driver.find_element_by_id(id).text
                            print(self.from_station, '至', self.to_station, self.train_date, t, i, current_td)
                            if current_td != '无' and current_td != '--':
                                print('发现有余票啦！')
                                orderBotton = current_ge[0].find_element_by_class_name('btn72')
                                orderBotton.click()
                                # 等待所有的乘客信息被加载完毕
                                WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH,".//ul[@id = 'normal_passenger_id']/li")))
                                # 获取所有的乘客信息
                                passanger_labels = self.driver.find_elements_by_xpath(".//ul[@id = 'normal_passenger_id']/li/label")
                                for passanger_label in passanger_labels:  # 遍历所有的label标签
                                    name = passanger_label.text
                                    if name in self.passengers:  # 判断名字是否与之前输入的名字重合
                                        passanger_label.click()  # 执行点击选中操作

                                # 获取提交订单的按钮
                                submitBotton = self.driver.find_element_by_id('submitOrder_id')
                                submitBotton.click()

                                # 显示等待确人订单对话框是否出现
                                WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME,'dhtmlx_wins_body_outer')))
                                # 显示等待确认按钮是否加载出现，出现后执行点击操作
                                WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.ID,'qr_submit_id')))
                                ConBotton = self.driver.find_element_by_id('qr_submit_id')
                                ConBotton.click()
                                try:
                                    while ConBotton:
                                        ConBotton.click()
                                        ConBotton = self.driver.find_element_by_id('qr_submit_id')
                                except Exception as e:
                                    pass
                                # 发送抢票成功邮件
                                content = "成功抢到 {} {} {} 次车票，快去支付吧~".format(self.train_date, t, i)
                                self.sendEmail(content)
                                return '抢票成功啦！'
                    self.totalFlush += 1
                    # 转化时间显示格式
                    m, s = divmod(time.time() - self.startTime, 60)
                    h, m = divmod(m, 60)
                    totalTime = "%02d:%02d:%02d" % (h, m, s)
                    print('————————已运行{}s，累计抢票{}次——————————'.format(totalTime, self.totalFlush))

                else:
                    print('网络好像开了小差，正在努力刷新～')
                    self.driver.refresh()  # 刷新页面
                    time.sleep(1)
        except Exception as e:
            self.driver.quit()
            print('程序异常停止：')
            print(e)
            content = "程序异常停止,错误信息：{}".format(e)
            self.sendEmail(content)


    def run(self):
        self.login()
        self.wait_input()
        self._order_ticket()
        # self.sendEmail(self.train_date, 'K111', '硬卧')


if __name__ == '__main__':
    spider = Qiangpiao(0)
    spider.run()