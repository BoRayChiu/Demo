"""There are some Crawler for crawling Dcard.

Browser: Create a Firefox WebDriver.
DcardSeleniumCrawler: Crawl the website it gets.
DcardTopicsIdCrawler: Get topic ids.
DcardPostCrawler: Get meta informations and contents of a topic.
DcardCommentsCrawler: Get comments.
DcardSubCommentsCrawler: Get SubComments.
"""

import datetime
import json
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from webdriver_manager.firefox import GeckoDriverManager


class Browser:
    """Create a Firefox WebDriver."""

    def __init__(self):
        """
        Browser is 
            1. Headless
            2. Disable gpu
            3. The latest Firefox version

        Typical usage example:
            browser = Browser().browser 
        """
        opts = Options()
        opts.add_argument('--headless')
        opts.add_argument('--disable-gpu')
        service = Service(GeckoDriverManager().install())
        self.browser = webdriver.Firefox(service=service, options=opts)


class DcardSeleniumCrawler:
    """Crawl the website it gets.

    Attributes:
        browser: The browser be used to crawl website.
    """

    def __init__(self, browser):
        self._browser = browser
        self._url = ""
        self._original_result = []

    def _crawl(self):
        """Browse the url and save the json result."""
        self._browser.get(self._url)
        time.sleep(5)
        try:
            json_button = self._browser.find_element(By.CSS_SELECTOR, "#rawdata-tab")
        except:
            print("Cloudflare!")
            time.sleep(3600)
        finally:
            self._browser.find_element(By.CSS_SELECTOR, "#rawdata-tab").click()
            res = self._browser.find_element(
                By.CSS_SELECTOR, "#rawdata-panel pre.data").text
        self._original_result = json.loads(res)


class DcardTopicsIdCrawler(DcardSeleniumCrawler):
    """Get topic ids.

    Inherit from DcardSeleniumCrawler.

    Attributes:
        browser: The browser be used to crawl website.
        board: The board we want to crawl.
        frequency: The number of topics we want to get.
    """

    def __init__(self, browser, board: str, frequency: str):
        super().__init__(browser)
        self._url = "".join(
            (
                "https://www.dcard.tw/service/api/v2/forums/",
                board,
                "/posts?limit=",
                frequency
            )
        )

    @property
    def result(self) -> list:
        """Return the topic ids.

        Get the topic ids which put in the json result we get from website.

        Returns:
            A list is formed with topic ids and 
            their type are string.
            For example: 
            ['12345', '54321']
        """
        self._crawl()
        topic_ids = []
        for i in range(len(self._original_result)):
            topic_ids.append(str(self._original_result[i].get("id")))
        return topic_ids


class DcardPostCrawler(DcardSeleniumCrawler):
    """DcardPostCrawler: Get meta informations and contents of a topic.

    Inherit from DcardSeleniumCrawler.

    Attributes:
        browser: The browser be used to crawl website.
        topic_id: The id of topic we wnat to crawl.
    """

    def __init__(self, browser, topic_id: str):
        super().__init__(browser)
        self._url = "".join(
            (
                "https://www.dcard.tw/service/api/v2/",
                "posts/",
                topic_id
            )
        )

    @property
    def result(self):
        """Return the topic.

        Get the topic information(meta informations and contents) 
        which put in the json result we get from website.

        Returns:
            A dict that keys are category and values are information.
            For example: 
                {
                    'MetaInformation':
                    {
                        'Author': 'Kevin', 
                        'AuthorID': '12345', 
                        'Title': 'Something', 
                        'Time': '2023-03-21 02:57:29'
                    }
                    'Contents': 'Something'
                }
        """
        self._crawl()
        topic = {}
        meta_information = {}
        # User Information
        school = self._original_result.get("school")
        department = self._original_result.get("department")
        # If "withNickname" is True, then user is not anonymous.
        if (self._original_result.get("withNickname") is True):
            meta_information["Author"] = school
            meta_information["AuthorID"] = department
        else:
            meta_information["School"] = school
            meta_information["Department"] = department
        # Title
        meta_information["Title"] = self._original_result.get("title")
        # Created time
        meta_information["Time"] = normalization_time(
            self._original_result.get("createdAt")[0:19])
        # Contents
        topic["Contents"] = self._original_result.get("content").replace(
            "\n", " ")
        # Meta Information
        topic["MetaInformation"] = meta_information
        return topic


class DcardCommentsCrawler(DcardSeleniumCrawler):
    """DcardCommentsCrawler: Get comments.

    Inherit from DcardSeleniumCrawler.

    Attributes:
        browser: The browser be used to crawl website.
        topic_id: The id of topic we wnat to crawl.
    """

    def __init__(self, browser, topic_id: str):
        super().__init__(browser)
        self._url = "".join(
            (
                    "https://www.dcard.tw/service/api/v2/",
                    "posts/",
                    topic_id,
                    "/comments"
            )
        )

    @property
    def result(self):
        """Return the comments list.

        Get the comments of topic 
        which put in the json result we get from website.

        Returns:
            A list is formed with
            some dicts keys that are category and values are information.
            For example: 
                [
                    {
                        'ID': 'abc321', 
                        'Author': 'Kevin', 
                        'AuthorID': '12345', 
                        'Contents': 'Something'
                    }
                ]
        """
        self._crawl()
        comments_list = []
        for i in range(len(self._original_result)):
            comment = {}
            # CommentID, save for crawling subcomments.
            id = self._original_result[i].get("id")
            comment["ID"] = id
            # If content is None, then comment has been removed.
            content = self._original_result[i].get("content")
            if (content is None):
                continue
            # User Inforamtion
            school = self._original_result[i].get("school")
            department = self._original_result[i].get("department")
            # If "withNickname" is True, then user is not anonymous.
            if (self._original_result[i]["withNickname"] is True):
                comment["Author"] = school
                comment["AuthorID"] = department
            else:
                comment["School"] = school
                comment["Department"] = department
            # Content
            comment["Contents"] = content.replace("\n", " ")
            # SubComments(could be None)
            comment["SubComments"] = []
            # Determine if have sub comments.
            if (self._original_result[i].get("subCommentCount") > 0):
                comment["hasSubComments"] = True
            else:
                comment["hasSubComments"] = False
            comments_list.append(comment)
        return comments_list


class DcardSubCommentsCrawler(DcardSeleniumCrawler):
    """DcardCommentsCrawler: Get subcomments.

    Inherit from DcardSeleniumCrawler.

    Attributes:
        browser: The browser be used to crawl website.
        topic_id: The id of topic we wnat to crawl.
        parent_comment_id: The id of the comment which subcomments reply.
    """

    def __init__(self, browser, topic_id: str, parent_comment_id: str):
        super().__init__(browser)
        self._url = "".join(
            (
                "https://www.dcard.tw/service/api/v2/",
                "posts/",
                topic_id,
                "/comments",
                "?parentId=",
                parent_comment_id
            )
        )
        self.__parent_comment_id = parent_comment_id

    @property
    def result(self):
        """Return the subcomments list.

        Get the subcomments of specified comment of a topic 
        which put in the json result we get from website.

        Returns:
            A list is formed with
            some dicts keys that are category and values are information.
            For example: 
                [
                    {
                        'ParentCommentID': 'abc321', 
                        'Author': 'Kevin', 
                        'AuthorID': '12345', 
                        'Contents': 'Something'
                    }
                ]
        """
        self._crawl()
        subcomments_list = []
        for i in range(len(self._original_result)):
            subcomment = {}
            # Parent Comment ID
            subcomment["ParentCommentID"] = self.__parent_comment_id
            # If content is None, then comment has been removed.
            content = self._original_result[i].get("content")
            if (content is None):
                continue
            # User Information
            school = self._original_result[i].get("school")
            department = self._original_result[i].get("department")
            # If "withNickname" is True, then user is not anonymous.
            if (self._original_result[i]["withNickname"] is True):
                subcomment["Author"] = school
                subcomment["AuthorID"] = department
            else:
                subcomment["School"] = school
                subcomment["Department"] = department
            # Content
            subcomment["Contents"] = content.replace("\n", " ")
            subcomments_list.append(subcomment)
        return subcomments_list
    
def normalization_time(time:str):
    """Set time format '%Y-%m-%d %H:%M:%S'.
    
    Args:
        time: The time wnat to formatted.
    Returns:
        A time which type is string.
        For example:
            '2023-03-21 02:57:29'
    """
    dt = datetime.datetime.fromisoformat(time)
    formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
    return formatted_time


if __name__ == "__main__":
    browser = Browser().browser
    d = DcardPostCrawler(browser, "241539400")
    print(d.result)
