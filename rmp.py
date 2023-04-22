from typing import Union, List, Dict
import httpx
import re
import sys
import os
from termcolor import cprint
from getkey import getkey
import json
from rich.console import Console
from rich.markdown import Markdown
import requests
import base64
import shutil

console = Console()

dir_path = os.path.dirname(os.path.realpath(__file__))
config_path = os.path.join(dir_path, 'browser.json')

with open(config_path, 'r') as f:
    data = json.load(f)
    u_agent = data["user_agent"]
    num_pages = data["num_pages"]

def search(query: str, num: int = num_pages, headers: Union[Dict[str, str], None] ={"User-Agent":
                u_agent}) -> List[Union[dict, str]]:

    results: List[Union[dict, str]] = []

    base_url: str = "https://www.google.com/search?q={}&num=30&hl=en"

    page: str = httpx.get(base_url.format(query), headers=headers).text

    web: str = '<div class="yuRUbf"><a href="(.*?)" data-jsarwt=".*?" ' \
                   'data-usg=".*?" data-ved=".*?"><br><h3 class="LC20lb MBeuO DKV0Md">(.*?)</h3>.*?' \
                   '<div class="VwiC3b yXK7lf MUxGbd yDYNvb lyLwlc lEBKkf" style="-webkit-line-clamp:2">' \
                   '<span>(.*?)</span></div>'

    for i in re.findall(pattern=web, string=page):
        if i[0].startswith('https://github.com'):
          if len(i[0].split('/')) == 5:
            results.append({
                "url": i[0],
                "title": i[1],
                "description": re.sub('<[^<>]+>', '', i[2])
            })

    return results[:num if len(results) > num else len(results)]

def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def trunc_desc(string):
    out = (string[:155] + '..') if len(string) > 157 else string
    return out

def print_item(item,i):
    cprint(f"{item['title']}", "blue")
    cprint(f"{trunc_desc(item['description'])}", "white")
    cprint(f"[{i}]: {item['url']}\n", "green")

def show_results(page):
    for i, res in enumerate(split_res[page]):
        print_item(res,i+1)

def show_page(page):
    global pagination
    os.system('clear')
    show_results(page)
    if len(split_res[page]) == 5:
        print(f"Showing results {page*5 + 1} - {page*5 + 5}")
    else:
        print(f"Showing results {page*5 + 1} - {page*5 + len(split_res[page])} (last entry)")

    print("Enter [1-5] to open README, [n/p] for next/previous results, or [q] to quit")

    while True:
        key = getkey()
        if key.isdigit() and int(key) > 0 and int(key) < 6:
            break
        elif key in ('n', 'p', 'q'):
            break
        else:
            continue

    if key.isdigit():
        i = int(key)
        gitUrl = split_res[page][i-1]['url']
        getReadme(gitUrl)

    elif key == 'n':
        pagination += 1
        if pagination > len(split_res)-1:
            pagination = len(split_res)-1
        show_page(pagination)
    elif key == 'p':
        pagination -= 1
        if pagination < 0:
            pagination = 0
        show_page(pagination)
    elif key == 'q':
        os.system('clear')
        exit(0)

def getReadme(gitUrl):
    os.system('clear') 
    urlParts = gitUrl.split('/')
    user = urlParts[3]
    repo = urlParts[4]
    rawUrl = f"https://api.github.com/repos/{user}/{repo}/contents/README.md"
    req = requests.get(rawUrl)
    if req.status_code == requests.codes.ok:
        req = req.json()
        byte_content = base64.b64decode(req['content'])
        content = byte_content.decode("utf-8")
        showReadme(content)
    else:
        print('Sorry, no README file found...')
        exit(0)

def showReadme(content):
    os.system('clear')
    totalLines = content.splitlines()
    viewLines = shutil.get_terminal_size().lines - 3
    cols = shutil.get_terminal_size().columns
    startLine = 0
    if len(totalLines) <= viewLines:
        console.print(Markdown(content))
    else:
        prettyPrintLines(startLine,viewLines+1,totalLines,cols)
        while True:
            key = getkey()
            if key == 'n':
                if viewLines+startLine < len(totalLines):
                    startLine += viewLines-2
                    os.system('clear')
                    prettyPrintLines(startLine,viewLines+startLine,totalLines,cols)
            elif key == 'p':
                if startLine > 0:
                    startLine -= viewLines+2
                    if startLine < 0:
                        startLine = 0;
                    os.system('clear')
                    prettyPrintLines(startLine,viewLines+startLine,totalLines,cols)
            elif key == 'q':
                os.system('clear')
                exit(0)

def prettyPrintLines(start,end,lines,cols):
    md = ''
    for i in range(start,end):
        if i < len(lines):
            md += f"{lines[i]}\n"
    console.print(Markdown(md))
    print('\n')
    print('-' * cols)
    print('Press [n/p] for scrolling, or [q] to quit.')

pagination = 0
args = sys.argv
args[0] = 'github'
if len(args) > 1:
    query = " ".join(args)
    results = search(query)
    split_res = list(chunks(results,5))
    show_page(pagination)
else:
    print("Seems like you're not looking for anything. By then...")