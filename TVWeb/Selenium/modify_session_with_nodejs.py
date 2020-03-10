"""
Modify TiledViz sessions with Selenium
"""

import os,sys,time
import logging
import argparse

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.events import EventFiringWebDriver, AbstractEventListener
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary

LOGIN_="ddurandi"
PASSWORD_="OtherP@ssw/31d"
SESSION_="TestSession"
NBTILESET_=1

def parse_args(argv):
    parser = argparse.ArgumentParser(
        'From a (users,project,session) get tile_sets, tiles and connections tables and build a session json structure from TiledViz database.')
    parser.add_argument('-l','--login', default=LOGIN_,
                         help='Login in TiledViz (default: '+LOGIN_+')')
    parser.add_argument('-p', '--password', default=PASSWORD_,
                         help='User password (default: '+PASSWORD_+')')
    parser.add_argument('-s', '--session', default=SESSION_,
                         help='TiledViz session (default: '+SESSION_+')')
    parser.add_argument('-o', '--mysession', action='store_true',
                         help='Is it my own session.')
    parser.add_argument('-i', '--invitedsession', action='store_true',
                         help='I am working with one of my invited session.)')
    parser.add_argument('-n', '--nbtileset', default=NBTILESET_, type=int,
                         help='Number of tilesets to be modified (default: '+str(NBTILESET_)+')')
    parser.add_argument('tilesetmodifs', nargs="*",
                         help='''
                         List of modifications : for each tileset
                          tileset name
                          path to nodes.js file (with filename)''')

    args = parser.parse_args(argv[1:])
    return args

# # Wait Nsec after each call
# Nsec = 4

class MyListener(AbstractEventListener):
    pass
    # global Nsec
    # def before_navigate_to(self, url, driver):
    #     print("Before navigate to %s" % url)
    # def after_navigate_to(self, url, driver): #.get(self.URL)
    #     time.sleep(Nsec)
    #     print("After navigate to %s" % url)
    # def after_click(self, url, driver):
    #     time.sleep(Nsec)
    #     print("After click to %s" % url)

#URL = 'http://flaskdock:5000'

# chrome_options = webdriver.ChromeOptions()
# driver = webdriver.Chrome(chrome_options=chrome_options)

URL = 'http://localhost:5000'
try:
   firefox_profile = webdriver.FirefoxProfile()
   driver = webdriver.Firefox(firefox_profile=firefox_profile)
except Exception as e:
   print("erreur ",e.msg)
   
finddriver = EventFiringWebDriver(driver, MyListener())

args = parse_args(sys.argv)
# if (args.enablejsonwrite):
#     print("Json output file enable :",args.jsonfile)

driver.get(URL)
assert "TiledViz" in driver.title

driver.get_cookies()


LoginPage = finddriver.find_element_by_xpath("//button[@name='buttonLogin']")
LoginPage.click()
assert "Login TiledViz" in driver.title

testform={"username":args.login,"password":args.password}
for t in testform:
    inputElement = finddriver.find_element_by_id(t)
    inputElement.clear()
    inputElement.send_keys(testform[t])
    
remember_me=finddriver.find_element_by_id("remember_me")
remember_me.click()

choose_session=finddriver.find_element_by_xpath("//input[@id='choice_project-1']")
choose_session.click()

el = finddriver.find_element_by_id("submit")
el.click()

assert "All projects/sessions TiledViz" in driver.title

my_own_session=args.mysession
if ( my_own_session ):
    sessionfilter = finddriver.find_element_by_id("filter_chosen_project_session")
    goButton = finddriver.find_element_by_id("Valid_chosen_project_session")
    sessionfilter.click()
else:
    sessionfilter = finddriver.find_element_by_id("filter_chosen_session_invited")
    goButton = finddriver.find_element_by_id("Valid_chosen_session_invited")
    sessionfilter.click()

sessionfilter.send_keys(args.session)
goButton.click()

edit_session = finddriver.find_element_by_xpath('//input[@value="Edit session before grid"]')
edit_session.click()

assert "Edit session TiledViz" in driver.title



for ts in range(args.nbtileset):
    
    idTileset=args.tilesetmodifs[2*ts]
    print("Modifying Tileset "+idTileset)

    choose_ts=finddriver.find_element_by_xpath("//label[contains(., '"+idTileset+"')]/input")
    choose_ts.click()

    #//form[@id='login-form']/input[@id='edit']
    #edit_ts = finddriver.find_element_by_xpath('//input[@value="Edit session TiledViz"]')
    edit_ts = finddriver.find_element_by_xpath("//form[@id='login-form']/input[@id='edit']")
    edit_ts.click()
    
    elem=finddriver.find_element_by_xpath("//textarea[@id='json_tiles_text']")
    elem.clear()

    #driver.findElement(By.cssSelector("body")).sendKeys(Keys.chord(Keys.CONTROL, "a"));
    #driver.findElement(By.xpath("//body")).sendKeys(Keys.chord(Keys.CONTROL, "a"));
    
    # elem.send_keys("{\"nodes\": [  \n {\n   \"url\": \"https://upload\"IdLocation\": -1} ]}")
    # elem.send_keys(Keys.ENTER)
    jsfile=args.tilesetmodifs[2*ts+1]
    try:
        fdfile=open(jsfile)
    except Exception as e :
        print("Can't open file "+jsfile)
        break;
    data=fdfile.read()
    driver.execute_script("var textnode = document.getElementById('json_tiles_text'); "+
                         "textnode.value = arguments[0];",
                         data);
    el = finddriver.find_element_by_id("submit")
    el.click()
    time.sleep(1)
    
driver.quit() 
