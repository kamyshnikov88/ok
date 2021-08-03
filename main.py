import pytesseract
import time
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.safari.webdriver import WebDriver
import pandas as pd
import cv2
import urllib.request as urllib
import ssl
import os


def click(element: WebElement) -> None:
    element.click()
    time.sleep(2)


def create_https_context() -> None:
    try:
        _create_unverified_https_context = ssl._create_unverified_context
    except AttributeError:
        pass
    else:
        ssl._create_default_https_context = _create_unverified_https_context


def get_driver(w_h: int, w_w: int) -> WebDriver:
    driver = webdriver.Safari()
    driver.set_window_size(w_h, w_w)
    driver.get('https://ok.ru/')
    return driver


def log_in(driver: WebDriver) -> None:
    log_form = driver.find_element_by_css_selector('#field_email')
    log_form.send_keys('9099054549')  # input login

    pass_form = driver.find_element_by_css_selector('#field_password')
    pass_form.send_keys('rfhiowfe[-wefijof34-HU(*^$-2', Keys.ENTER)
    time.sleep(2)


def get_search_list(driver: WebDriver, query: str) -> None:
    (driver.get('https://ok.ru/dk?st.cmd=searchResult&'
                'st.mode=Content&st.grmode=Groups&'
                'st.query=' + query + '&st.cphoto=With'))


def get_posts(driver: WebDriver) -> list:
    last_post = None
    posts = (driver.
             find_elements_by_css_selector('div.'
                                           'row__px8cs.'
                                           'skip-first-gap__m3nyy.'
                                           'content-tab-item__m3nyy'))
    while last_post != posts[-1]:
        driver.execute_script('window.scrollTo(0,document.body.scrollHeight);')
        time.sleep(.6)
        driver.execute_script('arguments[0].scrollIntoView();', posts[-1])
        time.sleep(.6)

        last_post = posts[-1]
        posts = (driver.
                 find_elements_by_css_selector('div.'
                                               'row__px8cs.'
                                               'skip-first-gap__m3nyy.'
                                               'content-tab-item__m3nyy'))
    return posts


def get_image(element: WebElement, path: str) -> None:
    url = element.get_attribute('src')
    urllib.urlretrieve(url, path)


def get_text(path: str) -> str:
    image = cv2.imread(path)
    text = (pytesseract
            .image_to_string(image, lang='rus')
            .replace('\n', ' ')
            .lower())
    return ' '.join(text.split())


def write_link(p_link: list) -> None:
    info = (driver.find_element_by_css_selector('div.'
                                                'media-layer.'
                                                'js-viewport-container.'
                                                'media-layer__topic.'
                                                '__v2.'
                                                '__active.'
                                                '__process-transparent.'
                                                '__new-closing')
            .get_attribute('data-l'))
    group_id = info.split(',')[-1].split('"')[-2]
    topic_id = info.split(',')[0].split('"')[-2]
    p_link.append('https://ok.ru/group/' + group_id + '/topic/' + topic_id)


def check_targets(collage: list, driver: WebDriver, targets: list) -> None:
    # select post
    click(collage[0])

    # check post contain image
    mpi = driver.find_elements_by_css_selector('.media-photos_img')

    if mpi:
        get_image(mpi[0], './temp.jpg')
        text = get_text('./temp.jpg')
        for target in targets:
            if target in text:
                write_link(posts_to_df)
                break
        # hide post
        click(driver.find_element_by_css_selector('div.ic.'
                                                  'media-layer_close_ico'))


if __name__ == '__main__':
    queries = pd.read_csv('queries.csv')['query']
    targets = pd.read_csv('targets.csv')['target']
    posts_to_df = []

    create_https_context()
    driver = get_driver(1000, 900)
    log_in(driver)
    for query in queries:
        get_search_list(driver, query)
        posts = get_posts(driver)
        for post in posts:
            # check what post collage contains only 1 element (__single)
            collage = post.find_elements_by_css_selector('div.collage.__single')
            if collage:
                # skip posts that crash script
                if ('responsive' in collage[0].get_attribute('class') or
                        collage[0].find_elements_by_css_selector('.gif_hld')):
                    continue

                check_targets(collage, driver, targets)
    driver.quit()
    os.remove('temp.jpg')

    # to csv
    df = pd.DataFrame({'post': posts_to_df}).to_csv(path='./result.csv')
