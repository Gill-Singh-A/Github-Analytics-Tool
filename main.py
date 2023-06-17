#! /usr/bin/env python3

import requests
from bs4 import BeautifulSoup

class Github:
    github = "https://github.com/"
    repoTab = "?tab=repositories&page="
    def __init__(self, ID):
        self.id = ID
        self.home_page_link = f"{Github.github}{self.id}/"
        self.home_page = requests.get(self.home_page_link)
        self.home_page_html = BeautifulSoup(self.home_page.content, "html.parser")
        if self.home_page.status_code == 200:
            self.found = True
        else:
            self.found = False
        self.repoCount = self.getRepoCount()
    def getRepoCount(self):
        counter = self.home_page_html.find("span", attrs={"class": "Counter"})
        return int(counter.text)
    def getRepos(self):
        repos = []
        while len(repos) != self.repoCount:
            repo_page_link = f"{Github.github}{self.id}{Github.repoTab}{len(repos)//30+1}"
            repo_page = requests.get(repo_page_link)
            repo_page_html = BeautifulSoup(repo_page.content, "html.parser")
            repositories = repo_page_html.find_all(itemprop="name codeRepository")
            for repository in repositories:
                repos.append({"name": repository.get_attribute_list(key="href")[0].split('/')[-1], "link": f"{self.home_page_link}{repository.get_attribute_list(key='href')[0].split('/')[-1]}"})
        return repos

if __name__ == "__main__":
    pass