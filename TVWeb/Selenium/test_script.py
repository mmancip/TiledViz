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
        self.driver = webdriver.Chrome(chrome_options=chrome_options)

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
            elem.send_keys("TestSession")
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

            elem.send_keys("{\"nodes\": [  \n {\n   \"url\": \"https://upload.wikimedia.org/wikipedia/commons/thumb/0/04/Lophornis_ornatus%2C_la_coqueta_adornada_o_coqueta_abanico_canela_-_Regina_Gabilondo_Toscano.jpg/512px-Lophornis_ornatus%2C_la_coqueta_adornada_o_coqueta_abanico_canela_-_Regina_Gabilondo_Toscano.jpg\",\n   \"title\": \"Lophornis ornatus - Regina Gabilondo Toscano\", \n   \"name\": \"Lophornis_ornatus\", \n   \"comment\": \"title=Regina Gabilondo Toscano [CC BY-SA 3.0], via Wikimedia Commons https://commons.wikimedia.org/wiki/File:Lophornis_ornatus,_la_coqueta_adornada_o_coqueta_abanico_canela_-_Regina_Gabilondo_Toscano.jpg\", \n   \"connection\": 0, \n   \"pos_px_x\":-1, \n   \"pos_px_y\":-1, \n   \"IdLocation\": -1},  \n {\n   \"url\": \"https://upload.wikimedia.org/wikipedia/commons/thumb/2/28/Las_aves_de_Cali_-_Gloria_Sthefany_Muriel_Lorza.jpg/640px-Las_aves_de_Cali_-_Gloria_Sthefany_Muriel_Lorza.jpg\",\n   \"title\": \"Las aves de Cali - Gloria Sthefany Muriel Lorza\", \n   \"name\": \"Las aves de Cali\", \n   \"comment\": \"title=Gloria Sthefany Muriel Lorza [CC BY-SA 3.0], via Wikimedia Commons https://commons.wikimedia.org/wiki/File:Las_aves_de_Cali_-_Gloria_Sthefany_Muriel_Lorza.jpg\", \n   \"connection\": 0, \n   \"pos_px_x\":-1, \n   \"pos_px_y\":-1, \n   \"IdLocation\": -1},  \n {\n   \"url\": \"https://upload.wikimedia.org/wikipedia/commons/thumb/6/65/Amanecer_-_Jos%C3%A9_Luis_Ortega_Gir%C3%B3n.jpg/543px-Amanecer_-_Jos%C3%A9_Luis_Ortega_Gir%C3%B3n.jpg\",\n   \"title\": \"Amanecer - José Luis Ortega Giron\", \n   \"name\": \"Amanecer\", \n   \"comment\": \"title=José Luis Ortega Girón [CC BY-SA 3.0], via Wikimedia Commons https://commons.wikimedia.org/wiki/File:Amanecer_-_José_Luis_Ortega_Girón.jpg\", \n   \"connection\": 0, \n   \"pos_px_x\":-1, \n   \"pos_px_y\":-1, \n   \"IdLocation\": -1},  \n {\n   \"url\": \"https://upload.wikimedia.org/wikipedia/commons/thumb/9/9f/Cardenal_norte%C3%B1o_-_Northern_cardinal_-_Cardinalis_cardinalis_-_Ester_G%C3%B3mez_Serra.jpg/640px-Cardenal_norte%C3%B1o_-_Northern_cardinal_-_Cardinalis_cardinalis_-_Ester_G%C3%B3mez_Serra.jpg\",\n   \"title\": \"Cardinalis cardinalis - Ester Gómez Serra\", \n   \"name\": \"Cardinalis cardinalis\", \n   \"comment\": \"title=Ester Gómez Serra [CC BY-SA 3.0], via Wikimedia Commons https://commons.wikimedia.org/wiki/File:Cardenal_norteño_-_Northern_cardinal_-_Cardinalis_cardinalis_-_Ester_Gómez_Serra.jpg\", \n   \"connection\": 0, \n   \"pos_px_x\":-1, \n   \"pos_px_y\":-1, \n   \"IdLocation\": -1},  \n {\n   \"url\": \"https://upload.wikimedia.org/wikipedia/commons/thumb/e/e3/Canis_lupus_occidentalis_%28Etapas_de_crecimiento%29_-_Miren_Leyzaola.jpg/640px-Canis_lupus_occidentalis_%28Etapas_de_crecimiento%29_-_Miren_Leyzaola.jpg\", \n   \"title\": \"Canis lupus occidentalis (Etapas de crecimiento) - Miren Leyzaola\", \n   \"name\": \"Canis lupus occidentalis\", \n   \"comment\": \"title=Miren Leyzaola [CC BY-SA 3.0], via Wikimedia Commons https://commons.wikimedia.org/wiki/File:Canis_lupus_occidentalis_(Etapas_de_crecimiento)_-_Miren_Leyzaola.jpg\", \n   \"connection\": 0, \n   \"pos_px_x\":-1, \n   \"pos_px_y\":-1, \n   \"IdLocation\": -1},  \n {\n   \"url\": \"https://upload.wikimedia.org/wikipedia/commons/thumb/6/63/Cats_-_Adrienn_Pomper.jpg/640px-Cats_-_Adrienn_Pomper.jpg\", \n   \"title\": \"Cats - Adrienn Pomper\", \n   \"name\": \"Cats\", \n   \"comment\": \"title=Adrienn Pomper [CC BY-SA 3.0], via Wikimedia Commons https://commons.wikimedia.org/wiki/File:Cats_-_Adrienn_Pomper.jpg\", \n   \"connection\": 0, \n   \"pos_px_x\":-1, \n   \"pos_px_y\":-1, \n   \"IdLocation\": -1},  \n {\n   \"url\": \"https://upload.wikimedia.org/wikipedia/commons/thumb/6/64/Colibri_coruscans_-_David_Barrag%C3%A1n.jpg/640px-Colibri_coruscans_-_David_Barrag%C3%A1n.jpg\", \n   \"title\": \"Colibri coruscans - David Barragán\", \n   \"name\": \"Colibri coruscans\", \n   \"comment\": \"title=David Barragán [CC BY-SA 3.0], via Wikimedia Commons https://commons.wikimedia.org/wiki/File:Colibri_coruscans_-_David_Barragán.jpg\", \n   \"connection\": 0, \n   \"pos_px_x\":-1, \n   \"pos_px_y\":-1, \n   \"IdLocation\": -1},  \n {\n   \"url\": \"https://upload.wikimedia.org/wikipedia/commons/thumb/1/13/Corvus_corax_-_Carolina_Fuentes.jpg/640px-Corvus_corax_-_Carolina_Fuentes.jpg\", \n   \"title\": \"Corvus corax - Carolina Fuentes\", \n   \"name\": \"Corvus corax\", \n   \"comment\": \"title=Carolina Fuentes [CC BY-SA 3.0], via Wikimedia Commons https://commons.wikimedia.org/wiki/File:Corvus_corax_-_Carolina_Fuentes.jpg\", \n   \"connection\": 0, \n   \"pos_px_x\":-1, \n   \"pos_px_y\":-1, \n   \"IdLocation\": -1},  \n {\n   \"url\": \"https://upload.wikimedia.org/wikipedia/commons/7/7b/Fiery-throated_hummingbird_-_Amber_Hudson-Peacock.jpg\", \n   \"title\": \"Fiery-throated hummingbird - Amber Hudson-Peacock\", \n   \"name\": \"Fiery-throated hummingbird\", \n   \"comment\": \"title=Amber Hudson-Peacock [CC BY-SA 3.0], via Wikimedia Commons https://commons.wikimedia.org/wiki/File:Fiery-throated_hummingbird_-_Amber_Hudson-Peacock.jpg\", \n   \"connection\": 0, \n   \"pos_px_x\":-1, \n   \"pos_px_y\":-1, \n   \"IdLocation\": -1},  \n {\n   \"url\": \"https://upload.wikimedia.org/wikipedia/commons/thumb/a/a0/Kingfisher_-_Karolina_Kijak.jpg/724px-Kingfisher_-_Karolina_Kijak.jpg\", \n   \"title\": \"Kingfisher - Karolina Kijak\", \n   \"name\": \"Kingfisher\", \n   \"comment\": \"title=Karolina Kijak [CC BY-SA 3.0], via Wikimedia Commons https://commons.wikimedia.org/wiki/File:Kingfisher_-_Karolina_Kijak.jpg\", \n   \"connection\": 0, \n   \"pos_px_x\":-1, \n   \"pos_px_y\":-1, \n   \"IdLocation\": -1},  \n {\n   \"url\": \"https://upload.wikimedia.org/wikipedia/commons/thumb/a/a6/Pionus_chalcopterus_%28Cotorra_Maicera_o_Loro_Alibronceado%29_-_Valeria_Tisn%C3%A9s_Londo%C3%B1o.jpg/682px-Pionus_chalcopterus_%28Cotorra_Maicera_o_Loro_Alibronceado%29_-_Valeria_Tisn%C3%A9s_Londo%C3%B1o.jpg\", \n   \"title\": \"Pionus_chalcopterus_-_Valeria_Tisnés_Londoño\", \n   \"name\": \"Pionus_chalcopterus\", \n   \"comment\": \"title=Valeria Tisnés Londoño [CC BY-SA 3.0], via Wikimedia Commons https://commons.wikimedia.org/wiki/File:Pionus_chalcopterus_(Cotorra_Maicera_o_Loro_Alibronceado)_-_Valeria_Tisn%C3%A9s_Londo%C3%B1o.jpg\", \n   \"connection\": 0, \n   \"pos_px_x\":-1, \n   \"pos_px_y\":-1, \n   \"IdLocation\": -1},  \n {\n   \"url\": \"https://upload.wikimedia.org/wikipedia/commons/thumb/f/fc/Mart%C3%ADn_Pescador_%28Alcedo_atthis%29_-_Gloria_Cosculluela_Moreno.jpg/640px-Mart%C3%ADn_Pescador_%28Alcedo_atthis%29_-_Gloria_Cosculluela_Moreno.jpg\", \n   \"title\": \"Martín Pescador (Alcedo atthis) - Gloria Cosculluela Moreno\", \n   \"name\": \"Martín Pescador\", \n   \"comment\": \"title=Gloria Cosculluela Moreno [CC BY-SA 3.0], via Wikimedia Commons https://commons.wikimedia.org/wiki/File:Martín_Pescador_(Alcedo_atthis)_-_Gloria_Cosculluela_Moreno.jpg\", \n   \"connection\": 0, \n   \"pos_px_x\":-1, \n   \"pos_px_y\":-1, \n   \"IdLocation\": -1},  \n {\n   \"url\": \"https://upload.wikimedia.org/wikipedia/commons/thumb/3/3e/Onychorhynchus_coronatus_-_Anastasiya_Sulimova.jpg/508px-Onychorhynchus_coronatus_-_Anastasiya_Sulimova.jpg\", \n   \"title\": \"Onychorhynchus coronatus - Anastasiya Sulimova\", \n   \"name\": \"Onychorhynchus coronatus\", \n   \"comment\": \"title=Anastasiya Sulimova [CC BY-SA 3.0], via Wikimedia Commons https://commons.wikimedia.org/wiki/File:Onychorhynchus_coronatus_-_Anastasiya_Sulimova.jpg\", \n   \"connection\": 0, \n   \"pos_px_x\":-1, \n   \"pos_px_y\":-1, \n   \"IdLocation\": -1},  \n {\n   \"url\": \"https://upload.wikimedia.org/wikipedia/commons/thumb/3/34/Iguana_Azul_-_Carolina_Linares_Barrag%C3%A1n.jpg/640px-Iguana_Azul_-_Carolina_Linares_Barrag%C3%A1n.jpg\", \n   \"title\": \"Iguana Azul - Carolina Linares Barragá\", \n   \"name\": \"Iguana Azul\", \n   \"comment\": \"title=Carolina Linares Barragán [CC BY-SA 3.0], via Wikimedia Commons https://commons.wikimedia.org/wiki/File:Iguana_Azul_-_Carolina_Linares_Barragán.jpg\", \n   \"connection\": 0, \n   \"pos_px_x\":-1, \n   \"pos_px_y\":-1, \n   \"IdLocation\": -1},  \n {\n   \"url\": \"https://upload.wikimedia.org/wikipedia/commons/thumb/e/e3/Mirlo_%28Turdus_merula%29_-_Miguel_Correa_Yanguas.jpg/640px-Mirlo_%28Turdus_merula%29_-_Miguel_Correa_Yanguas.jpg\", \n   \"title\": \"Mirlo (Turdus merula) - Miguel Correa Yanguas\", \n   \"name\": \"Mirlo (Turdus merula)\", \n   \"comment\": \"title=Miguel Correa Yanguas [CC BY-SA 3.0], via Wikimedia Commons https://commons.wikimedia.org/wiki/File:Mirlo_(Turdus_merula)_-_Miguel_Correa_Yanguas.jpg\", \n   \"connection\": 0, \n   \"pos_px_x\":-1, \n   \"pos_px_y\":-1, \n   \"IdLocation\": -1},  \n {\n   \"url\": \"https://upload.wikimedia.org/wikipedia/commons/thumb/a/a0/Microcebus_murinus_-_Estefan%C3%ADa_Padull%C3%A9s.jpg/528px-Microcebus_murinus_-_Estefan%C3%ADa_Padull%C3%A9s.jpg\", \n   \"title\": \"Microcebus murinus - Estefanía Padullés\", \n   \"name\": \"Microcebus murinus\", \n   \"comment\": \"title=Estefanía Padullés [CC BY-SA 3.0], via Wikimedia Commons https://commons.wikimedia.org/wiki/File:Microcebus_murinus_-_Estefanía_Padullés.jpg\", \n   \"connection\": 0, \n   \"pos_px_x\":-1, \n   \"pos_px_y\":-1, \n   \"IdLocation\": -1},  \n {\n   \"url\": \"https://upload.wikimedia.org/wikipedia/commons/thumb/6/67/Peque%C3%B1as_aves_-_Roc_Oliv%C3%A9_Pous.jpg/640px-Peque%C3%B1as_aves_-_Roc_Oliv%C3%A9_Pous.jpg\", \n   \"title\": \"Pequeñas aves - Roc Olivé Pous\", \n   \"name\": \"Pequeñas aves\", \n   \"comment\": \"title=Roc Olivé Pous [CC BY-SA 3.0], via Wikimedia Commons https://commons.wikimedia.org/wiki/File:Pequeñas_aves_-_Roc_Olivé_Pous.jpg\", \n   \"connection\": 0, \n   \"pos_px_x\":-1, \n   \"pos_px_y\":-1, \n   \"IdLocation\": -1},  \n {\n   \"url\": \"https://upload.wikimedia.org/wikipedia/commons/thumb/c/cf/Phallichthys_tico_-_Jos%C3%A9_Fabricio_Vargas_Murillo.jpg/640px-Phallichthys_tico_-_Jos%C3%A9_Fabricio_Vargas_Murillo.jpg\", \n   \"title\": \"Phallichthys tico - José Fabricio Vargas Murillo\", \n   \"name\": \"Phallichthys tico\", \n   \"comment\": \"title=José Fabricio Vargas Murillo [CC BY-SA 3.0], via Wikimedia Commons https://commons.wikimedia.org/wiki/File:Phallichthys_tico_-_Jos%C3%A9_Fabricio_Vargas_Murillo.jpg\", \n   \"connection\": 0, \n   \"pos_px_x\":-1, \n   \"pos_px_y\":-1, \n   \"IdLocation\": -1},  \n {\n   \"url\": \"https://upload.wikimedia.org/wikipedia/commons/thumb/3/37/Quetzal_-_Blanca_Gozalo_Lazaro.jpg/811px-Quetzal_-_Blanca_Gozalo_Lazaro.jpg\", \n   \"title\": \"Quetzal - Blanca Gozalo Lazaro\", \n   \"name\": \"Quetzal\", \n   \"comment\": \"title=Blanca Gozalo Lazaro [CC BY-SA 3.0], via Wikimedia Commons https://commons.wikimedia.org/wiki/File:Quetzal_-_Blanca_Gozalo_Lazaro.jpg\", \n   \"connection\": 0, \n   \"pos_px_x\":-1, \n   \"pos_px_y\":-1, \n   \"IdLocation\": -1},  \n {\n   \"url\": \"https://upload.wikimedia.org/wikipedia/commons/thumb/6/63/Upupa-epops.jpg/724px-Upupa-epops.jpg\", \n   \"title\": \"Upupa-epops\", \n   \"name\": \"Upupa-epops\", \n   \"comment\": \"title=Alfonso Escorial de Lucas [CC BY-SA 3.0], via Wikimedia Commons https://commons.wikimedia.org/wiki/File:Upupa-epops.jpg\", \n   \"connection\": 0, \n   \"pos_px_x\":-1, \n   \"pos_px_y\":-1, \n   \"IdLocation\": -1} ]}")
            elem.send_keys(Keys.ENTER)

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
