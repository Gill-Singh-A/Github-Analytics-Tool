#! /usr/bin/env python3

import requests
from bs4 import BeautifulSoup

class Github:
    github = "https://github.com/"
    repoTab = "?tab=repositories"
    followers = "?tab=followers"
    following = "?tab=following"
    achievement = "?tab=achievements"
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
                if parent_tag.get_attribute_list(key="href")[0] != None:
                    starRepos.append({"name": parent_tag.get_attribute_list(key="href")[0], "link": f"{Github.github}{parent_tag.get_attribute_list(key='href')[0]}"})
            next_link = None
            for a_tag in a_tags:
                if a_tag.text == "Next":
                    next_link = a_tag.get_attribute_list(key="href")[0]
                    break
        return starRepos
    def getLinks(self):
        links = []
        link_tags = self.home_page_html.find_all("a", attrs={"class": "Link--primary", "rel": "nofollow me"})
        for link_tag in link_tags:
            link = link_tag.get_attribute_list(key="href")[0]
            link_name = link.split('.')[1]
            link_name = f"{link_name[0].upper()}{link_name[1:]}"
            links.append({"name": link_name, "link": link})
        return links
    def VCardNames(self):
        name_info = {}
        vcard_names_tag = self.home_page_html.find("h1", attrs={"class": "vcard-names"})
        name = vcard_names_tag.find("span", attrs={"itemprop": "name"})
        nickname = vcard_names_tag.find("span", attrs={"itemprop": "additionalName"})
        pronouns = vcard_names_tag.find("span", attrs={"itemprop": "pronouns"})
        if name != None:
            name_info["name"] = name.text.strip()
        if nickname != None:
            name_info["nickname"] = nickname.text.strip()
        if pronouns != None:
            name_info["pronouns"] = pronouns.text.strip()
        return name_info
    def getWorkPlace(self):
        work_tag = self.home_page_html.find("li", attrs={"itemprop": "worksFor"})
        if work_tag != None:
            return work_tag.text.strip()
        return None
    def getLocalTimeZone(self):
        time_tag = self.home_page_html.find("li", attrs={"itemprop": "localTime"})
        if time_tag != None:
            return time_tag.text.strip().split('\n')[1].strip()
        return None
    def getLocation(self):
        location_tag = self.home_page_html.find("li", attrs={"itemprop": "homeLocation"})
        if location_tag != None:
            return location_tag.text.strip()
        return None
    def getBio(self):
        div_tags = self.home_page_html.find_all("div")
        for div_tag in div_tags:
            attribute_list = div_tag.get_attribute_list(key="class")
            for attribute in attribute_list:
                if type(attribute) == str:
                    if "bio" in attribute:
                        return div_tag.text
        return None
    def getAchievements(self):
        achievements = []
        achievement_page_link = f"{self.home_page_link}{Github.achievement}"
        achievement_page = requests.get(achievement_page_link)
        achievement_page_html = BeautifulSoup(achievement_page.content, "html.parser")
        achievement_tags = achievement_page_html.find_all("img", attrs={"class": "achievement-badge-card"})
        for achievement_tag in achievement_tags:
            parent_tag = list(achievement_tag.parents)[0]
            achievement = parent_tag.text.strip().split('\n')
            if len(achievement) == 1:
                achievements.append({"name": achievement[0], "count": 1})
            else:
                achievements.append({"name": achievement[0], "count": int(achievement[1][1:])})
        return achievements
    def isPro(self):
        pro_tag = self.home_page_html.find("span", attrs={"title": "Label: Pro"})
        if pro_tag == None:
            return False
        return True
    def getOrganization(self):
        organization_tags, organizations = [], []
        avatar_tags = self.home_page_html.find_all("img", attrs={"class": "avatar"})
        for avatar_tag in avatar_tags:
            if len(avatar_tag.get_attribute_list(key="class")) == 1:
                organization_tags.append(avatar_tag)
        for organization_tag in organization_tags:
            parent_tag = list(organization_tag.parents)[0]
            organization = {}
            organization["name"] = organization_tag.get_attribute_list(key="alt")[0][1:]
            link = parent_tag.get_attribute_list(key='href')[0]
            if link != None:
                organization["link"] = f"{Github.github}{link[1:]}"
            organizations.append(organization)
        return organizations
    def getStatus(self):
        status_tag = self.home_page_html.find("div", attrs={"class": "user-status-message-wrapper"})
        if status_tag != None:
            return status_tag.text.strip()
        return None
    def getMail(self):
        mail = self.home_page_html.find("li", attrs={"itemprop": "email"})
        if mail != None:
            return mail.text.strip()
        return None
    def getRepoBranchName(self, branch):
        branch_link = f"{self.home_page_link}/{branch}"
        branch_page = requests.get(branch_link)
        branch_html = BeautifulSoup(branch_page.content, "html.parser")
        branch_tag = branch_html.find("summary", attrs={"title": "Switch branches or tags"})
        return branch_tag.text.strip()

if __name__ == "__main__":
    pass