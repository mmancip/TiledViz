"""
Test TiledViz with Selenium
"""

import unittest
import os,sys,time
import logging

os.chdir("/tmp/tests")

# from pyvirtualdisplay import Display

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.events import EventFiringWebDriver, AbstractEventListener

os.system("ls -la /usr/local/Selenium/")

#logging.getLogger().setLevel(logging.INFO)

# display = Display(visible=0, size=(1920, 1080))
# display.start()

# Wait Nsec after each call
Nsec = 4

class MyListener(AbstractEventListener):
    global Nsec
    def before_navigate_to(self, url, driver):
        print("Before navigate to %s" % url)
    def after_navigate_to(self, url, driver): #.get(self.URL)
        time.sleep(Nsec)
        print("After navigate to %s" % url)
    def after_click(self, url, driver):
        time.sleep(Nsec)
        print("After click to %s" % url)

                                    
class TestTemplate(unittest.TestCase):
    """Include test cases on a given url"""

    URL = 'http://flaskdock:5000'

    def setUp(self):
        """Start web driver"""
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--enable-logging')
        chrome_options.add_argument('--enable-offline-auto-reload')
        chrome_options.add_argument('--enable-offline-auto-reload-visible-only')
        chrome_options.add_argument('--num-raster-threads=4')
        chrome_options.add_argument('--enable-main-frame-before-activation')
        chrome_options.add_argument('--enable-compositor-image-animations')
        
        #chrome_options.add_experimental_option('prefs', {
        #        'download.default_directory': os.getcwd(),
        #        'download.prompt_for_download': False,
        #    })

        #        logging.info('Prepared chrome options..')
        self.driver = webdriver.Chrome(options=chrome_options)

        # firefox_profile = webdriver.FirefoxProfile()
        # firefox_profile.set_preference('browser.download.folderList', 2)
        # firefox_profile.set_preference('browser.download.manager.showWhenStarting', False)
        # firefox_profile.set_preference('browser.download.dir', os.getcwd())
        # firefox_profile.set_preference('browser.helperApps.neverAsk.saveToDisk', 'text/csv')
    
        # # firefox_profile.set_preference("general.useragent.override", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_4) AppleWebKit/536.30.1 (KHTML, like Gecko) Version/6.0.5 Safari/536.30.1")
        # # firefox_profile.set_preference("webdriver.log.file", "webdriver.log")

        # logging.info('Prepared firefox profile..')
            
        # self.driver = webdriver.Firefox(firefox_profile=firefox_profile)

        self.driver.implicitly_wait(20)
        self.driver.set_window_size(1920, 1080)
        self.driver.maximize_window()

        # zoomAction = ActionChains(self.driver)
        # body = self.driver.find_element_by_tag_name('body')
        # for i in range(6):
        #     zoomAction.send_keys_to_element(body,Keys.CONTROL,"-").perform() # +Keys.MINUS
        # driver.get('chrome://settings/')
        # driver.execute_script('chrome.settingsPrivate.setDefaultZoom(1.5);')
        self.driver.execute_script("document.body.style.zoom='25%'")

        self.finddriver = EventFiringWebDriver(self.driver, MyListener())

        # logging.info('Initialized browser..')
        
                                
    def tearDown(self):
        """Stop web driver"""
        thedriver=self.driver
        thedriver.quit()

    def test_case_1(self):
        """Connect to server"""
        thedriver=self.driver
        finddriver=self.finddriver
        try:
            time.sleep(Nsec)
            thedriver.get(self.URL)
            assert "TiledViz" in thedriver.title
            thedriver.get_cookies()
            #print("\nsource :",thedriver.page_source)
            #assert "No results found." not in thedriver.page_source
        except NoSuchElementException as ex:
            self.fail(ex.msg+": \n"+thedriver.title)

    def test_case_2(self):
        """Find and click register button"""
        thedriver=self.driver
        finddriver=self.finddriver
        try:
            time.sleep(Nsec)
            thedriver.get(self.URL)
            el = finddriver.find_element_by_partial_link_text('Register')
            #el = finddriver.find_element_by_xpath("//button[@name='buttonRregister']")
            #el = finddriver.find_element_by_name('buttonRregister')
            el.click()

        except NoSuchElementException as ex:
            self.fail(ex.msg+": \n"+thedriver.title)

    def test_case_3(self):
        """Find and click login more button"""
        thedriver=self.driver
        finddriver=self.finddriver
        try:
            time.sleep(Nsec)
            thedriver.get(self.URL)
            # thedriver.get(self.URL+'/login')
            el = finddriver.find_element_by_partial_link_text('login')
            el.click()

            assert "Login TiledViz" in thedriver.title

            el = finddriver.find_element_by_id("username")
            #"//form[@id='loginForm']/input[1]")
            el.clear()
            el.send_keys("ddurandi")
            el.send_keys(Keys.RETURN)
            #el.send_keys(" and some", Keys.ARROW_DOWN)
            
            inputElement = finddriver.find_element_by_id("password")
            inputElement.clear()
            inputElement.send_keys("OtherP@ssw/31d")
            thedriver.save_screenshot('/tmp/tests/test-password1_screenshot.png')

            # el = finddriver.find_element_by_xpath("//input[@name='password']")
            # el.clear()
            # el.send_keys("OtherP@ssw/31d")
            # thedriver.save_screenshot('/tmp/tests/test-password2_screenshot.png')

            el = finddriver.find_element_by_id("submit")
            el.click()
            #el = finddriver.find_element_by_partial_link_text('submit')
            
            thedriver.save_screenshot('/tmp/tests/test-password3_screenshot.png')
            assert "All projects/sessions TiledViz" in thedriver.title
        except NoSuchElementException as ex:
            self.fail(ex.msg+": \n"+thedriver.title)

    def test_case_4(self):
        """Register new user"""
        thedriver=self.driver
        finddriver=self.finddriver
        try:
            time.sleep(Nsec)
            thedriver.get(self.URL+'/register')
            assert "TiledViz register" in thedriver.title
            testform={"username":"mmartin","password":"mvect22Y","email":"m.martin@gmel.com","compagny":"MaMDLS","manager":"MyBoss"}

            for t in testform:
                inputElement = finddriver.find_element_by_id(t)
                inputElement.clear()
                inputElement.send_keys(testform[t])
                #thedriver.save_screenshot('/tmp/tests/test-registred_{}_screenshot.png'.format(t))

            inputElement = finddriver.find_element_by_id("confirm")
            inputElement.clear()
            inputElement.send_keys(testform["password"])
            thedriver.save_screenshot('/tmp/tests/test-registred_confirm_screenshot.png')
                
            remember_me=self.finddriver.find_element_by_id("remember_me")
            remember_me.click()

            choice_project=self.finddriver.find_element_by_xpath('//input[@value="create"]')
            choice_project.click()
            
            thedriver.save_screenshot('/tmp/tests/test-registred1_screenshot.png')
            el = finddriver.find_element_by_id("submit")
            el.click()

            thedriver.save_screenshot('/tmp/tests/test-registred2_screenshot.png')
            assert "New project TiledViz" in thedriver.title
            
        except NoSuchElementException as ex:
            self.fail(ex.msg+": \n"+thedriver.title)


    def test_case_5(self):
        """An already registered user"""
        thedriver=self.driver
        finddriver=self.finddriver
        try:
            time.sleep(Nsec)
            thedriver.get(self.URL+'/register')
            assert "TiledViz register" in thedriver.title
            testform={"username":"ddurandi","password":"OtherP@ssw/31d","email":"dany.durandi@gmel.com","compagny":"MaMDLS","manager":"MyBoss"}
            for t in testform:
                inputElement = finddriver.find_element_by_id(t)
                inputElement.clear()
                inputElement.send_keys(testform[t])

            inputElement = finddriver.find_element_by_id("confirm")
            inputElement.clear()
            inputElement.send_keys(testform["password"])
            thedriver.save_screenshot('/tmp/tests/test-registred_confirm_screenshot.png')
                
            remember_me=self.finddriver.find_element_by_id("remember_me")
            remember_me.click()

            choice_project=self.finddriver.find_element_by_xpath('//input[@value="create"]')
            choice_project.click()

            thedriver.save_screenshot('/tmp/tests/test-already-registred1_screenshot.png')
            
            el = finddriver.find_element_by_id("submit")
            el.click()

            thedriver.save_screenshot('/tmp/tests/test-already-registred2_screenshot.png')

            assert "New project TiledViz" in thedriver.title

            testform={"projectname":"CLIMAF","description":"This project already exists."}
            for t in testform:
                inputElement = finddriver.find_element_by_id(t)
                inputElement.send_keys(testform[t])

            choice_project=self.finddriver.find_element_by_xpath('//input[@value="use"]')
            choice_project.click()
            thedriver.save_screenshot('/tmp/tests/test-already-registred3_screenshot.png')
            
            el = finddriver.find_element_by_id("submit")
            el.click()

            thedriver.save_screenshot('/tmp/tests/test-already-registred4_screenshot.png')

            #assert "New project TiledViz" in thedriver.title
            
        except NoSuchElementException as ex:
            self.fail(ex.msg+": \n"+thedriver.title)

    def test_case_6(self):
        """Login and create a new project/session/tileset."""
        thedriver=self.driver
        finddriver=self.finddriver
        try:
            time.sleep(Nsec)
            thedriver.get(self.URL)

            LoginPage = finddriver.find_element_by_xpath("//button[@name='buttonLogin']")
            LoginPage.click()
            assert "Login TiledViz" in thedriver.title
            testform={"username":"ddurandi","password":"OtherP@ssw/31d"}
            for t in testform:
                inputElement = finddriver.find_element_by_id(t)
                inputElement.clear()
                inputElement.send_keys(testform[t])

            remember_me=self.finddriver.find_element_by_id("remember_me")
            remember_me.click()

            create_project=self.finddriver.find_element_by_xpath("//input[@id='choice_project-0']")
            create_project.click()
            
            el = finddriver.find_element_by_id("submit")
            el.click()

            assert "project" in thedriver.current_url

            testform={"projectname":"TiledVizTEST","description":"Test for TiledViz with Wikimedia pictures"}
            for t in testform:
                inputElement = finddriver.find_element_by_id(t)
                inputElement.clear()
                inputElement.send_keys(testform[t])
            
            thedriver.save_screenshot('/tmp/tests/test6-project_screenshot.png')

            button=self.finddriver.find_element_by_xpath("//input[2][@id='submit']")
            button.click()
 
            button=self.finddriver.find_element_by_xpath("//div/input[@id='sessionname']")
            button.click()
 
            elem=self.finddriver.find_element_by_xpath("//input[@id='sessionname']")
            elem.clear()
            elem.send_keys("TestSelenium")
            elem.send_keys(Keys.TAB)
            
 
            button=self.finddriver.find_element_by_xpath("//div[2]/input[@id='description']")
            button.click()
 
            elem=self.finddriver.find_element_by_xpath("//input[@id='description']")
            elem.clear()
            elem.send_keys("Test Session for TiledViz with pictures")
            elem.send_keys(Keys.TAB)
            
            elem=self.finddriver.find_element_by_xpath("//input[@id='users-0']")
            elem.clear()
            elem.send_keys("ddurandi")
            elem.send_keys(Keys.TAB)
             
            elem=self.finddriver.find_element_by_xpath("//input[@id='users-1']")
            elem.clear()
            elem.send_keys("mmartial")
            elem.send_keys(Keys.TAB)
            
            thedriver.save_screenshot('/tmp/tests/test6-session1_screenshot.png')
 
            button=self.finddriver.find_element_by_xpath("//input[3][@id='Session_config']")
            button.click()

            thedriver.save_screenshot('/tmp/tests/test6-session_config_screenshot.png')

            # button=self.finddriver.find_element_by_xpath("//input[2][@id='editjson']")
            # button.click()
 
            # thedriver.save_screenshot('/tmp/tests/test6-jsoneditor_session1_screenshot.png')

            # button=self.finddriver.find_element_by_xpath("//tr[4]/td[3]/table/tbody/tr/td/button")
            # button.click()

            # thedriver.save_screenshot('/tmp/tests/test6-jsoneditor_session2_screenshot.png')
            # button=self.finddriver.find_element_by_xpath("//tr[8]/td[3]/table/tbody/tr/td/button")
            # button.click()

            # thedriver.save_screenshot('/tmp/tests/test6-jsoneditor_session3_screenshot.png')
            # button=self.finddriver.find_element_by_xpath("//tr[9]/td[3]/table/tbody/tr/td[4]/div")
            # button.click()

            # thedriver.save_screenshot('/tmp/tests/test6-jsoneditor_session4_screenshot.png')
            # button=self.finddriver.find_element_by_xpath("//tr[10]/td[3]/table/tbody/tr/td[4]/div")
            # button.click()

            # thedriver.save_screenshot('/tmp/tests/test6-jsoneditor_session5_screenshot.png')
            # button=self.finddriver.find_element_by_xpath("//tr[4]/td[3]/table/tbody/tr/td/button")
            # button.click()
 
            # thedriver.save_screenshot('/tmp/tests/test6-jsoneditor_session6_screenshot.png')

            # button=self.finddriver.find_element_by_xpath("//button[@id='submit']")
            # button.click()
 
            # thedriver.save_screenshot('/tmp/tests/test6-session2_screenshot.png')

            button=self.finddriver.find_element_by_xpath("//input[3][@id='submit']")
            button.click()

            thedriver.save_screenshot('/tmp/tests/test6-session3_screenshot.png')
            
            button=self.finddriver.find_element_by_xpath("//input[4][@id='submit']")
            button.click()
 
            elem=self.finddriver.find_element_by_xpath("//input[@id='name']")
            elem.clear()
            elem.send_keys("WikimediaTest")
            elem.send_keys(Keys.TAB)
             
            elem=self.finddriver.find_element_by_xpath("//input[@id='dataset_path']")
            elem.clear()
            elem.send_keys("upload.wikimedia.org")
            elem.send_keys(Keys.TAB)
            
            button=self.finddriver.find_element_by_xpath("//textarea[@id='json_tiles_text']")
            button.click()

            elem=self.finddriver.find_element_by_xpath("//textarea[@id='json_tiles_text']")
            elem.clear()

            # elem.send_keys("{\"nodes\": [  \n {...} ]}")
            # elem.send_keys(Keys.ENTER)
            jsfile="/usr/local/Selenium/TestSession.json"
            try:
                fdfile=open(jsfile)
            except Exception as e :
                print("Can't open file "+jsfile)
                sys.exit(1)
            data=fdfile.read()
            thedriver.execute_script("var textnode = document.getElementById('json_tiles_text'); "+
                         "textnode.value = arguments[0];",
                         data);

            thedriver.save_screenshot('/tmp/tests/test6-jsontext_screenshot.png')

            # button=self.finddriver.find_element_by_xpath("//input[2][@id='editjson']")
            # button.click()
 
            # thedriver.save_screenshot('/tmp/tests/test6-jsoneditor_tileset1_screenshot.png')

            # button=self.finddriver.find_element_by_xpath("//tr[2]/td[3]/table/tbody/tr/td/button")
            # button.click()
 
            # thedriver.save_screenshot('/tmp/tests/test6-jsoneditor_tileset2_screenshot.png')

            # button=self.finddriver.find_element_by_xpath("//tr[5]/td[3]/table/tbody/tr/td/button")
            # button.click()
 
            # thedriver.save_screenshot('/tmp/tests/test6-jsoneditor_tileset3_screenshot.png')

            # button=self.finddriver.find_element_by_xpath("//tr[7]/td[3]/table/tbody/tr/td[4]/div")
            # button.click()

            # thedriver.save_screenshot('/tmp/tests/test6-jsoneditor_tileset4_screenshot.png')

            # button=self.finddriver.find_element_by_xpath("//button[@id='submit']")
            # button.click()
 
            # thedriver.save_screenshot('/tmp/tests/test6-jsoneditor_tileset5_screenshot.png')

            button=self.finddriver.find_element_by_xpath("//input[3][@id='submit']")
            button.click()
 
            thedriver.save_screenshot('/tmp/tests/test6-end_build_session_screenshot.png')
            
        except NoSuchElementException as ex:
            self.fail(ex.msg+": \n"+thedriver.title)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestTemplate)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    sys.exit(not result.wasSuccessful())
