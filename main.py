#! /usr/bin/env python3

import requests
from bs4 import BeautifulSoup

class Github:
    github = "https://github.com/"
    repoTab = "?tab=repositories"
    followers = "?tab=followers"
    following = "?tab=following"
    stars = "?tab=stars"
    page = "page="
    def __init__(self, ID):
        self.id = ID
        self.home_page_link = f"{Github.github}{self.id}"
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
            repo_page_link = f"{self.home_page_link}/{Github.repoTab}&{Github.page}{len(repos)//30+1}"
            repo_page = requests.get(repo_page_link)
            repo_page_html = BeautifulSoup(repo_page.content, "html.parser")
            repositories = repo_page_html.find_all(itemprop="name codeRepository")
            for repository in repositories:
                repos.append({"name": repository.get_attribute_list(key="href")[0].split('/')[-1], "link": f"{self.home_page_link}/{repository.get_attribute_list(key='href')[0].split('/')[-1]}"})
        return repos
    def getFollowers(self):
        page_number, followers = 1, []
        followers_page_link = f"{self.home_page_link}/{Github.followers}&{Github.page}{page_number}"
        followers_page = requests.get(followers_page_link)
        followers_page_html = BeautifulSoup(followers_page.content, "html.parser")
        while True:
            follower_tags = followers_page_html.find_all("span", attrs={"class": "Link--secondary"})
            if len(follower_tags) == 0:
                break
            for follower_tag in follower_tags:
                followers.append(follower_tag.text)
            page_number += 1
            followers_page_link = f"{self.home_page_link}/{Github.followers}&{Github.page}{page_number}"
            followers_page = requests.get(followers_page_link)
            followers_page_html = BeautifulSoup(followers_page.content, "html.parser")
        return followers
    def getFollowing(self):
        page_number, following = 1, []
        following_page_link = f"{self.home_page_link}/{Github.following}&{Github.page}{page_number}"
        following_page = requests.get(following_page_link)
        following_page_html = BeautifulSoup(following_page.content, "html.parser")
        while True:
            follower_tags = following_page_html.find_all("span", attrs={"class": "Link--secondary"})
            if len(follower_tags) == 0:
                break
            for follower_tag in follower_tags:
                following.append(follower_tag.text)
            page_number += 1
            following_page_link = f"{self.home_page_link}/{Github.following}&{Github.page}{page_number}"
            following_page = requests.get(following_page_link)
            following_page_html = BeautifulSoup(following_page.content, "html.parser")
        return following
    def getStarRepos(self):
        starRepos = []
        next_link = f"{self.home_page_link}{Github.stars}"
        while next_link != None:
            star_page = requests.get(next_link)
            star_page_html = BeautifulSoup(star_page.content, "html.parser")
            a_tags = star_page_html.find_all("a")
            star_tags = star_page_html.find_all("span", attrs={"class": "text-normal"})
            for star_tag in star_tags:
                parent_tag = list(star_tag.parents)[0]
                if parent_tag.get_attribute_list(key="href")[0] != "None":
                    starRepos.append({"name": parent_tag.get_attribute_list(key="href")[0], "link": f"{Github.github}{parent_tag.get_attribute_list(key='href')[0]}"})
            next_link = None
            for a_tag in a_tags:
                if a_tag.text == "Next":
                    next_link = a_tag.get_attribute_list(key="href")[0]
                    break
        return starRepos

if __name__ == "__main__":
    pass