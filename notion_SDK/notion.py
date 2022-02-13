# %%
import json
from time import time
import ezdict
import requests
from ezdict import EZDict
from functools import cached_property
from copy import deepcopy
import json
from bs4 import BeautifulSoup
from tqdm import tqdm
import time


class Head2Block(object):
    def __init__(self, text=None) -> None:
        if text is None:
            text = []
        self._text = text
        self._payload= EZDict(
            EZDict(
                type="heading_2",
                heading_2 = {
                    "text": self._text
                }
            )
        )

    @property
    def json(self):
        self._payload[self._payload.type].text = [
            t.json for t in self._text
        ]
        return self._payload


class Head1Block(Head2Block):
    def __init__(self, text=None) -> None:
        if text is None:
            text = []
        self._text = text
        self._payload= EZDict(
            EZDict(
                type="heading_1",
                heading_1 = {
                    "text": self._text
                }
            )
        )


class Head3Block(Head2Block):
    def __init__(self, text=None) -> None:
        if text is None:
            text = []
        self._text = text
        self._payload= EZDict(
            EZDict(
                type="heading_3",
                heading_3 = {
                    "text": self._text
                }
            )
        )


class ParagraphBlock(object):
    def __init__(self, text=None) -> None:
        if text is None:
            text = []
        self._text = text
        self._payload= EZDict(
            EZDict(
                type="paragraph",
                paragraph=EZDict(
                    text=self._text
                )
            )
        )

    @property
    def json(self):
        self._payload.paragraph.text = [
            t.json for t in self._text
        ]
        return self._payload

class Text(object):
    def __init__(self, text=None, link=None) -> None:
        if not isinstance(text, str):
            raise TypeError("text must be a string")
        self._text = text
        self._payload= EZDict({
            "type": "text",
            "text": {
                "content": self._text,
                # "link": {
                #     "type": "url",
                #     "url": link,
                #     }
                }
            })
        if link is not None:
            self._payload.text.link = {
                "type": "url",
                "url": link,
            }

    @property
    def json(self):
        return self._payload


# class 


# %%
class Client(object):
    def __init__(self, token) -> None:
        self.url = "https://www.notion.so/api/v1/"
        self.token = token
    
    def get_me(self):
        resp = requests.get(
            'https://api.notion.com/v1/users/me', 
            headers={
                "Authorization": "Bearer " + self.token,
                "Notion-Version": "2021-08-16"})
        try:
            result = EZDict(resp.json())
            return result
        except Exception as e:
            print(e)
            return resp

    def get_users(self):
        resp = requests.get(
            'https://api.notion.com/v1/users?page_size=100',
            headers={
                "Authorization": "Bearer " + self.token,
                "Notion-Version": "2021-08-16"})
        try:
            result = EZDict(resp.json())
            return result
        except Exception as e:
            print(e)
            return resp
    
    def search(self):
        resp = requests.post(
            "https://api.notion.com/v1/search",
            headers={
                "Authorization": "Bearer " + self.token,
                "Notion-Version": "2021-08-16"},
            json={
                "page_size": 100,
            })
        try:
            result = EZDict(resp.json())
            return result
        except Exception as e:
            print(e)
            return resp

    def get_price_page_id(self):
        resp = self.search()
        for item in resp.results:
            item = EZDict(item)
            if item.properties.title.title[0]['plain_text'] == 'Papers':
                print('got it')
                return item.id
        return None
    
    def get_pages(self):
        resp = requests.post(
            'https://api.notion.com/v1/databases/database_id/query',
            headers={
                "Authorization": "Bearer " + self.token,
                "Notion-Version": "2021-08-16"})
        try:
            result = EZDict(resp.json())
            return result
        except Exception as e:
            print(e)
            return resp
    
    @cached_property
    def price_page(self):
        resp = self.search()
        for item in resp.results:
            item = EZDict(item)
            if item.properties.title.title[0]['plain_text'] == 'Papers':
                print('got it')
                return item
        return None

    @cached_property
    def price_page_id(self):
        return self.price_page.id

    def price_body(self):
        resp = requests.get(
            f'https://api.notion.com/v1/blocks/{self.price_page_id}/children?page_size=100',
            headers={
                "Authorization": "Bearer " + self.token,
                "Notion-Version": "2021-08-16"},
        )
        return resp
    
    def append_child(self, child):
        payload=dict(
            children=[
                child.json,
            ]
        )
        resp = requests.patch(
            f'https://api.notion.com/v1/blocks/{self.price_page_id}/children',
            json=payload,
            headers={
                "Authorization": "Bearer " + self.token,
                "Notion-Version": "2021-08-16"},
        )
        if resp.status_code == 200:
            return True
        else:
            raise Exception(resp.text)

    def append_h1(self, content='',link=None):
        child = Head1Block([Text(content, link)])
        return self.append_child(child)

    def append_h2(self, content='',link=None):
        child = Head2Block([Text(content, link)])
        return self.append_child(child)

    def append_h3(self, content='',link=None):
        child = Head3Block([Text(content, link)])
        return self.append_child(child)

    def append_paragraph(self, content=None, link=None):
        child = ParagraphBlock([Text(content, link=link)])
        return self.append_child(child)


# %%

def get_papers_today():
    url = 'https://arxiv.org/list/cs.AI/recent'
    resp = requests.get(url)
    soup = BeautifulSoup(resp.text, 'html.parser')
    items = soup.find('dl').findAll('dd')
    links = soup.find('dl').findAll('dt')
    collection = []

    for link, item in tqdm(zip(links, items), total=len(items)):
        title = item.find('div', {'class': "list-title mathjax"})
        title = list(title.children)[-1].strip()
        author = item.find('div', {'class': "list-authors"})
        author = [i.text for i in author.findAll('a')]
        author = ', '.join(author)
        abstract_link = link.find('a', dict(title="Abstract")).attrs['href']
        abstract_link = 'https://arxiv.org' + abstract_link
        abstract_page = BeautifulSoup(requests.get(abstract_link).content, 'html.parser')
        abstract = list(abstract_page.find('blockquote').children)[-1].strip().replace('\n', ' ')
        collection.append(EZDict(
            title=title,
            author=author,
            abstract=abstract,
            link=abstract_link,
        ))
    return collection


# %%
client = Client("secret_wfU9Nw26nRGnwugSBZZ3QZKRPUC4Oz3aNFoYH1eQmpe")
client.append_h1('papers today ' + time.strftime('%Y-%m-%d'))
# client.append_paragraph('papers today ' + time.strftime('%Y-%m-%d'))


# %%
papers_today = get_papers_today()

# %%
for paper in tqdm(papers_today):
    client.append_h3(paper.title, paper.link)
    client.append_paragraph(paper.author)
    client.append_paragraph(paper.abstract)
    client.append_paragraph("")

# %%
