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

#os.system("ls -la /usr/local/Selenium/")

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
        
        chrome_options.add_experimental_option('prefs', {
                'download.default_directory': os.getcwd(),
                'download.prompt_for_download': False,
            })

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
        self.driver.execute_script("document.body.style.webkitTransformOriginX=document.body.style.mstransformOriginX=document.body.style.transformOriginX=0;"+
                                   "document.body.style.webkitTransformOriginY=document.body.style.mstransformOriginY=document.body.style.transformOriginY=0;"+
                                   "document.body.style.webkitTransformOriginZ=document.body.style.mstransformOriginZ=document.body.style.transformOriginZ=0;"+
                                   "document.body.style.webkitTransform = document.body.style.msTransform = document.body.style.transform = 'scale(.25)'")

        self.finddriver = EventFiringWebDriver(self.driver, MyListener())

        # logging.info('Initialized browser..')
        
                                
    def tearDown(self):
        """Stop web driver"""
        thedriver=self.driver
        thedriver.quit()

    def test_case_7(self):
        """Login and test almost all the grid with the previous project."""
        thedriver=self.driver
        finddriver=self.finddriver
        try:
            time.sleep(Nsec)
            thedriver.get(self.URL)

            button=finddriver.find_element_by_xpath("//button[@name='buttonLogin']")
            button.click()
 
            elem=finddriver.find_element_by_xpath("//input[@id='username']")
            elem.clear()
            elem.send_keys("ddurandi")
            
            elem=finddriver.find_element_by_xpath("//input[@id='password']")
            elem.clear()
            elem.send_keys("OtherP@ssw/31d")
            
            remember_me=finddriver.find_element_by_id("remember_me")
            remember_me.click()
 
            button=finddriver.find_element_by_id('submit')
            button.click()
            
            elem=finddriver.find_element_by_id("filter_chosen_project_session")
            elem.send_keys("TestSelenium")

            button=finddriver.find_element_by_id('Valid_chosen_project_session')
            button.click()
 
            thedriver.save_screenshot('/tmp/tests/test7-which_session.png')

            #thedriver.set_window_size(8192, 4320)

            button=finddriver.find_element_by_id('submit')
            button.click()
            
            time.sleep(20)

            thedriver.save_screenshot('/tmp/tests/test7-Grid_screenshot.png')

            thedriver.execute_script("document.body.style.webkitTransformOriginX=document.body.style.mstransformOriginX=document.body.style.transformOriginX=0;"+
                                   "document.body.style.webkitTransformOriginY=document.body.style.mstransformOriginY=document.body.style.transformOriginY=0;"+
                                   "document.body.style.webkitTransformOriginZ=document.body.style.mstransformOriginZ=document.body.style.transformOriginZ=0;"+
                                   "document.body.style.webkitTransform = document.body.style.msTransform = document.body.style.transform = 'scale(.25)';"+
                                   "document.body.style.width='7680px';")
            thedriver.execute_script("document.body.style.margintop='-1220px'")
            thedriver.execute_script("document.body.style.marginleft='-2880px';")
            #thedriver.set_window_size(7680, 4320)
            thedriver.set_window_size(1920, 1080)
            thedriver.maximize_window()
            time.sleep(10)
            thedriver.save_screenshot('/tmp/tests/test7-Grid_unzoomed_screenshot.png')

            # print("Console :")
            # logging.debug(" Console :")
            # for entry in thedriver.get_log('browser'):
            #     print(str(entry))
            #     logging.debug(entry)
            

            button=finddriver.find_element_by_id("Globaloption8")
            thedriver.save_screenshot('/tmp/tests/test7-TileMenu.png')
            time.sleep(20)
            button.click()
            
            #thedriver.save_screenshot('/tmp/tests/test7-TileMenu.png')

            button=finddriver.find_element_by_id("0option1")
            time.sleep(2)
            button.click()
            time.sleep(6)


            thedriver.save_screenshot('/tmp/tests/test7-postIt.png')
            time.sleep(2)
            button.click()

            button=finddriver.find_element_by_id("1option0")
            button.click()

            time.sleep(2)
            button=finddriver.find_element_by_id('tile-opacity-1')
            time.sleep(2)
            button.click()
            
            slider=finddriver.find_element_by_id('tileOpacitySlider1')
            thedriver.save_screenshot('/tmp/tests/test7-opacity_before_screenshot.png')

            # #Using Action Class
            # move = ActionChains(finddriver);
            # move.move_to_element(slider);
            # move.move_by_offset(20, 0);
            # move.perform();
            # # Actions act=new Actions(driver);
            # # act.moveToElement(element).click().perform();

            button=finddriver.find_element_by_id('tileOpacitySlider1')
            button.click()

            thedriver.save_screenshot('/tmp/tests/test7-opacity_after_screenshot.png')
            
            button=finddriver.find_element_by_id('tile-opacity-1')
            button.click()
            

            button=finddriver.find_element_by_id("4option2")
            button.click()

            thedriver.save_screenshot('/tmp/tests/test7-draw_mode_screenshot.png')

            colorButton=finddriver.find_element_by_id('Drawoption0')
            colorButton.click()

            # colorChoose=finddriver.find_element_by_id('colorChoose')
            # colorChoose.click()
            # colorChoose.send_keys("#ea1d1d")

            colorButton=finddriver.find_element_by_id('Drawoption0')
            colorButton.click()

            canvas=finddriver.find_element_by_id('drawCanvas4')
            
            # #Using Action Class
            # move = ActionChains(thedriver)
            # move.move_to_element_with_offset(canvas,200,200);
            # move.click_and_hold(canvas[0])
            # move.move_by_offset(70, -55)
            # move.release(canvas)
            # move.perform()
            
            thedriver.save_screenshot('/tmp/tests/test7-draw_screenshot.png')
 
            saveOnTileButton=finddriver.find_element_by_id('Drawoption4')
            saveOnTileButton.click()

            time.sleep(4)

            button=finddriver.find_element_by_id("Globaloption6")
            button.click()

            button=finddriver.find_element_by_id("managementGlobaloption0")
            button.click()        
            
            thedriver.save_screenshot('/tmp/tests/test7-draw_management_screenshot.png')

            button=finddriver.find_element_by_id("Globaloption6")
            button.click()

            button=finddriver.find_element_by_id("6option4")
            button.click()

            button=finddriver.find_element_by_id("12option4")
            button.click()

            button=finddriver.find_element_by_id("3option3")
            button.click()

            button=finddriver.find_element_by_id("5option3")
            button.click()

            thedriver.save_screenshot('/tmp/tests/test7-lines_columns_exchange_screenshot.png')
            
            button=finddriver.find_element_by_id("Globaloption8")
            button.click()
            
            button=finddriver.find_element_by_id("Globaloption5")
            button.click()
            
            button=finddriver.find_element_by_id("zoomGlobaloption0")
            button.click()
            
            hitbox0=finddriver.find_element_by_id('hitbox0')
            hitbox0.click()
            # move = ActionChains(thedriver)
            # move.move_to_element(hitbox0)
            # move.click(hitbox0)
            # move.perform()
            time.sleep(2)
            
 
            hitbox1=finddriver.find_element_by_id('hitbox1')
            hitbox1.click()
            # move = ActionChains(thedriver)
            # move.move_to_element(hitbox1)
            # move.click(hitbox1)
            # move.perform()
            time.sleep(2)
            
            hitbox5=finddriver.find_element_by_id('hitbox5')
            hitbox5.click()
            # move = ActionChains(thedriver)
            # move.move_to_element(hitbox5)
            # move.click(hitbox5)
            # move.perform()
            time.sleep(2)
            
 
            hitbox4=finddriver.find_element_by_id('hitbox4')
            hitbox4.click()
            # move = ActionChains(thedriver)
            # move.move_to_element(hitbox4)
            # move.click(hitbox4)
            # move.perform()
            time.sleep(2)

            thedriver.save_screenshot('/tmp/tests/test7-select_0_1_4_5_screenshot.png')
            
            button=finddriver.find_element_by_id("Zoomoption0")
            button.click()
            
            time.sleep(2)

            thedriver.save_screenshot('/tmp/tests/test7-Zoom_screenshot.png')
            
            button=finddriver.find_element_by_id('Zclose2')
            button.click()
            
 
            button=finddriver.find_element_by_id('Zclose0')
            button.click()
            
            thedriver.save_screenshot('/tmp/tests/test7-zclose_screenshot.png')
            
            button=finddriver.find_element_by_id('buttonUnzoom')
            button.click()
            
 
            button=finddriver.find_element_by_id("Globaloption5")
            button.click()
            
            # button=finddriver.find_element_by_xpath("//div[3]/div[5][@id='option4']")
            # button.click()
 
            # button=finddriver.find_element_by_xpath("//div[8][@id='option7']")
            # button.click()
 
            # button=finddriver.find_element_by_id('onoff11')
            # button.click()
            
 
            # button=finddriver.find_element_by_id('onoff13')
            # button.click()
            
 
            # button=finddriver.find_element_by_id('onoff8')
            # button.click()
            
 
            # button=finddriver.find_element_by_xpath("//div[3]/div[4][@id='option3']")
            # button.click()
 
            # button=finddriver.find_element_by_xpath("//div[4]/div")
            # button.click()
 
            # time.sleep(1)

            # button=finddriver.find_element_by_id('Off')
            # button.click()
            
            # #thedriver.save_screenshot('/tmp/tests/test7-select_Off_tag_screenshot.png')
 
            # button=finddriver.find_element_by_xpath("//div[3]/div[5][@id='option4']")
            # button.click()
 
            # button=finddriver.find_element_by_xpath("//div[6]/div")
            # button.click()
 
            # #thedriver.save_screenshot('/tmp/tests/test7-Zoom_tag_Off_screenshot.png')
 
            # button=finddriver.find_element_by_id('buttonUnzoom')
            # button.click()
            
            # time.sleep(2)

            # button=finddriver.find_element_by_xpath("//div[4]/div")
            # button.click()
 
            # button=finddriver.find_element_by_xpath("//div[3]/div[5][@id='option4']")
            # button.click()
 
            # button=finddriver.find_element_by_xpath("//div[4]/div[2]")
            # button.click()
 
            # button=finddriver.find_element_by_id('Off')
            # button.click()
            
            # #thedriver.save_screenshot('/tmp/tests/test7-sort_Off_screenshot.png')
 

            # button=finddriver.find_element_by_xpath("//div[4]/div[2]")
            # button.click()
 
            # button=finddriver.find_element_by_xpath("//div[10][@id='option9']")
            # button.click()

            # #thedriver.save_screenshot('/tmp/tests/test7-QRcodes_screenshot.png')
 
            # button=finddriver.find_element_by_xpath("//div[10][@id='option9']")
            # button.click()
 
            # button=finddriver.find_element_by_xpath("//div[9][@id='option8']")
            # button.click()
 
            # time.sleep(1)

            # button=finddriver.find_element_by_id('zoomNode9')
            # button.click()
            
            # #thedriver.save_screenshot('/tmp/tests/test7-Zoom_on_node9_screenshot.png')

            # button=finddriver.find_element_by_id('buttonUnzoom')
            # button.click()
            
            # time.sleep(1)
 
            # button=finddriver.find_element_by_xpath("//div[3]/div[4]")
            # button.click()
 
            # button=finddriver.find_element_by_xpath("//div[@id='menu999']/div[11]")
            # move = ActionChains(thedriver)
            # move.move_to_element(button)
            # move.click(button)
            # move.perform()
 
            # #thedriver.save_screenshot('/tmp/tests/test7-info_node_always_show_screenshot.png')
 
            # button=finddriver.find_element_by_xpath("//div[@id='menu999']/div[11]")
            # move = ActionChains(thedriver)
            # move.move_to_element(button)
            # move.click(button)
            # move.perform()
            # # button=finddriver.find_element_by_xpath("//div[@id='menu999']/div[11]")
            # # button.click()
 
            # # button=finddriver.find_element_by_xpath("//div[15][@id='option14']")
            # # move = ActionChains(thedriver)
            # # move.move_to_element(button)
            # # move.click(button)
            # # move.perform()
 
            # # #thedriver.save_screenshot('/tmp/tests/test7-save_Session_screenshot.png')
 
            # # button=finddriver.find_element_by_id('submitSave')
            # # button.click()
            
            # # #thedriver.save_screenshot('/tmp/tests/test7-validate_save_screenshot.png')

            # # button=finddriver.find_element_by_id('gGsubmit')
            # # button.click()
             
            # # #thedriver.save_screenshot('/tmp/tests/test7-change_new_Session_screenshot.png')

            # # button=finddriver.find_element_by_id('ChangeRoomYes')
            # # button.click()
            
            # # #thedriver.save_screenshot('/tmp/tests/test7-validate_new_room_screenshot.png')


            # button=finddriver.find_element_by_xpath("//div[16][@id='option15']")
            # #button.click()
            # move = ActionChains(thedriver)
            # move.move_to_element(button)
            # move.click(button)
            # move.perform()

            # time.sleep(1)
            # #thedriver.save_screenshot('/tmp/tests/test7-options_screenshot.png')

            # button=finddriver.find_element_by_id('colNumber')
            # button.click()
            
 
            # elem=finddriver.find_element_by_xpath("//input[@id='colNumber']")
            # elem.clear()
            # elem.send_keys("4")
            # elem.send_keys(Keys.TAB)
            
 
            # button=finddriver.find_element_by_id('spreadX')
            # button.click()
            
 
            # elem=finddriver.find_element_by_xpath("//input[@id='spreadX']")
            # elem.clear()
            # elem.send_keys("1758.4")
            # elem.send_keys(Keys.TAB)
            

            # button=finddriver.find_element_by_id('spreadY')
            # button.click()
            
 
            # elem=finddriver.find_element_by_xpath("//input[@id='spreadY']")
            # elem.clear()
            # elem.send_keys("880")
            # elem.send_keys(Keys.TAB)
            
 
            # button=finddriver.find_element_by_xpath("//div/div/input[@name='color-theme-radio']")
            # button.click()
            
            # button=finddriver.find_element_by_id('showinfo-cb')
            # button.click()

            # #thedriver.save_screenshot('/tmp/tests/test7-save_options_screenshot.png')

            # button=finddriver.find_element_by_id('buttonSave')
            # button.click()
 
            # button=finddriver.find_element_by_xpath("//div[11][@id='option10']")
            # button.click()

            # #thedriver.save_screenshot('/tmp/tests/test7-info_screenshot.png')
 
            # button=finddriver.find_element_by_xpath("//div[12][@id='option11']")
            # button.click()

            # #thedriver.save_screenshot('/tmp/tests/test7-refrash_screenshot.png')
            
            # button=finddriver.find_element_by_xpath("//div[17][@id='option16']")
            # button.click()

            # #thedriver.save_screenshot('/tmp/tests/test7-help_TiledViz_screenshot.png')

            # slider=finddriver.find_element_by_xpath("//input[@id='helpSlider']")
            # #Using Action Class
            # move = ActionChains(thedriver);
            # move.move_to_element(slider);
            # move.move_by_offset(80, 0);
            # move.perform();

            # slider.click()
            
            # #thedriver.save_screenshot('/tmp/tests/test7-help_TiledViz_screenshot.png')

            # button=finddriver.find_element_by_id('buttonClosehelp')
            # button.click()
            
            # #thedriver.save_screenshot('/tmp/tests/test7_final_screenshot.png')
            
        except NoSuchElementException as ex:
            self.fail(ex.msg+": \n"+thedriver.title)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestTemplate)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    sys.exit(not result.wasSuccessful())
