import asyncio
import json
import os
import time

from ptt_crawler import PTTCrawler
from dcard_selenium_crawler import Browser
from dcard_selenium_crawler import DcardPostCrawler
from dcard_selenium_crawler import DcardCommentsCrawler
from dcard_selenium_crawler import DcardTopicsIdCrawler
from dcard_selenium_crawler import DcardSubCommentsCrawler
from baha_crawler import TopicIdCrawler
from baha_crawler import ThreadCrawler

def ptt_crawler(board:str, frequency:str):
    """Call PTT Crawler.
    
    Args:
        board: The board we want to crawl.
        frequency: The number of pages we want to get.
    Returns:
        A list is formed with some dict that keys are category and values are information.
        For example: 
            [
                {
                    'MetaInformation': 
                    {
                        'Author': 'bca321 (bcderf)',
                        'Title': '[閒聊] HELLO WORLD!',
                        'Time': '2023-03-21 02:57:29'
                    }
                    'Contents': 'Hello World :P'
                    'Messages': {'abc123': 'HAHA.'}
                }
            ]
    """
    # Create a Event Loop.
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    # Call PTTCrawler and pass parameters.
    crawler = PTTCrawler(board, frequency, loop)
    loop.run_until_complete(crawler.main())
    result = crawler.get_result()
    return result

def dcard_crawler(board:str, frequency:str):
    """Call Dcard Crawler.
    
    Args:
        board: The board we want to crawl.
        frequency: The number of topics we want to get.
    Returns:
        A list is formed with some dict that keys are category and values are information.
        For example: 
            [
                {
                    'MetaInformation':
                    {
                        'Author': 'Kevin', 
                        'AuthorID': '12345', 
                        'Title': 'Something', 
                        'Time': '2023-03-21 02:57:29'
                    }
                    'Contents': 'Something'
                    'Comments':             
                    [
                        {
                            'ID': 'abc321', 
                            'Author': 'Kevin', 
                            'AuthorID': '12345', 
                            'Contents': 'Something'
                        }
                    ]
                    'SubComments':
                    [
                        {
                            'ParentCommentID': 'abc321', 
                            'Author': 'Kevin', 
                            'AuthorID': '12345', 
                            'Contents': 'Something'
                        }
                    ]
                }
            ]
    """
    result = []
    browser = Browser().browser
    # Find topic ids
    dcard_topics_id_crawler = DcardTopicsIdCrawler(
        browser, board, frequency)
    wanted_topic_ids = dcard_topics_id_crawler.result
    time.sleep(30)
    for topic_id in wanted_topic_ids:
        res = {}
        # Post
        dcard_post_crawler = DcardPostCrawler(browser, topic_id)
        res = dcard_post_crawler.result
        time.sleep(30)
        # Comments
        dcard_comments_crawler = DcardCommentsCrawler(
            browser, topic_id)
        res["Comments"] = []
        res["SubComments"] = []
        comments_list = dcard_comments_crawler.result
        time.sleep(30)
        for i in range(comments_list):
            res["Comments"].append(comments_list[i])
            if comments_list[i]["has SubComments"] == True:
                dcard_sub_comments_crawler = DcardSubCommentsCrawler(
                    browser, topic_id, comments_list[i]["id"])
                res["SubComments"].append(
                    dcard_sub_comments_crawler.result)
                time.sleep(30)
        result.append(res)
    return result

def baha_crawler(board_id: str, frequency: int):
    """Call Baha Crawler.
    
    Args:
        board_id: The board id we want to crawl.
        frequency: The number of pages we want to get.
    Returns:
        A dicts keys that are category and values are information.
        For example: 
            [
                {
                    'Title': 'Hello World!'
                    'Topics': [
                        {
                            'Author': 'abc123', 
                            'Time': '2023-03-28 00:01:05', 
                            'Contents': 'Hello World HAHA', 
                            'Messages': [
                                {
                                    'Author': 'cba321', 
                                    'Time': '2023-03-29 23:51:42', 
                                    'Contents': 'HAHA'
                                }
                            ]
                        }
                    ]
                }
            ]
    """
    result = []
    topic_id_crawler = TopicIdCrawler(board_id, frequency)
    wanted_topic_ids = topic_id_crawler.result
    for topic_id in wanted_topic_ids:
        thread_crawler = ThreadCrawler(board_id, topic_id)
        result.append(thread_crawler.result)
    return result

def main():
    # PTT
    print("PTT start!")
    ptt_board = ["nCoV2019", "allergy", "Anti-Cancer", "Doctor-Info", "elderly", "MonkeyPox", "regimen", "Health", "MuscleBeach"]
    ptt_res = []
    for board in ptt_board:
        for r in ptt_crawler(board, "10"):
            ptt_res.append(r)
    # Baha
    print("Baha start!")
    baha_board = ["70091"]
    baha_result = []
    for board in baha_board:
        for r in baha_crawler(board, 1):
            baha_result.append(r)
    # Dcard
    print("Dcard start!")
    dcard_board = ["facelift", "2019_ncov", "fitness"]
    dcard_res = []
    for board in dcard_board:
        for r in dcard_crawler(board, "30"):
            dcard_res.append(r)
    # Get date.
    today = time.strftime("%Y-%m-%d")
    data = {
        "crawl_date": today,
        "PTT": ptt_res,
        "Dcard": dcard_res,
        "Baha": baha_result
    }
    return data