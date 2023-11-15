#! /usr/bin/env python3

import requests, os
from pathlib import Path
from datetime import date
from subprocess import run
from bs4 import BeautifulSoup
from datetime import datetime
from optparse import OptionParser
from pickle import dump, load
from colorama import Fore, Back, Style
from time import strftime, localtime, sleep, time

status_color = {
    '+': Fore.GREEN,
    '-': Fore.RED,
    '*': Fore.YELLOW,
    ':': Fore.CYAN,
    ' ': Fore.WHITE
}
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.5615.50 Safari/537.36",
    "Connection": "close",
    "DNT": "1"
}

def display(status, data, start='', end='\n'):
    print(f"{start}{status_color[status]}[{status}] {Fore.BLUE}[{date.today()} {strftime('%H:%M:%S', localtime())}] {status_color[status]}{Style.BRIGHT}{data}{Fore.RESET}{Style.RESET_ALL}", end=end)

def get_arguments(*args):
    parser = OptionParser()
    for arg in args:
        parser.add_option(arg[0], arg[1], dest=arg[2], help=arg[3])
    return parser.parse_args()[0]

month_indexes = {
    "January": 1,
    "February": 2,
    "March": 3,
    "April": 4,
    "May": 5,
    "June": 6,
    "July": 7,
    "August": 8,
    "September": 9,
    "October": 10,
    "November": 11,
    "December": 12
}

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
        self.home_page_user = requests.get(self.home_page_link, headers=headers)
        self.home_page_html = BeautifulSoup(self.home_page.content, "html.parser")
        self.home_page_user_html = BeautifulSoup(self.home_page.content, "html.parser")
        if self.home_page.status_code == 200:
            self.found = True
        else:
            self.found = False
            return
        self.repoCount = self.getRepoCount()
    def getRepoCount(self):
        counters = self.home_page_user_html.find_all("span", attrs={"class": "Counter"})
        for counter in counters:
            try:
                return int(counter.text)
            except:
                pass
    def getRepos(self, verbose=False):
        repos = []
        while len(repos) != self.repoCount:
            repo_page_link = f"{self.home_page_link}/{Github.repoTab}&{Github.page}{len(repos)//30+1}"
            repo_page = requests.get(repo_page_link, headers=headers)
            repo_page_html = BeautifulSoup(repo_page.content, "html.parser")
            repositories = repo_page_html.find_all(itemprop="name codeRepository")
            for repository in repositories:
                repo_link = f"{self.home_page_link}/{repository.get_attribute_list(key='href')[0].split('/')[-1]}"
                repo_page = requests.get(repo_link, headers=headers)
                repos.append({"name": repository.get_attribute_list(key="href")[0].split('/')[-1],
                              "link": f"{self.home_page_link}/{repository.get_attribute_list(key='href')[0].split('/')[-1]}",
                              "default_branch": self.getRepoDefaultBranch(repository.get_attribute_list(key="href")[0].split('/')[-1], repo_page=repo_page),
                              "branch_count": self.getRepoBranchCount(repository.get_attribute_list(key="href")[0].split('/')[-1], repo_page=repo_page),
                              "commits": self.getRepoCommitCount(repository.get_attribute_list(key="href")[0].split('/')[-1], repo_page=repo_page),
                              "about": self.getRepoAbout(repository.get_attribute_list(key="href")[0].split('/')[-1], repo_page=repo_page),
                              "star_users": self.getRepoStarUsers(repository.get_attribute_list(key="href")[0].split('/')[-1]),
                              "watchers": self.getRepoWatchers(repository.get_attribute_list(key="href")[0].split('/')[-1]),
                              "forks": self.getRepoForkCount(repository.get_attribute_list(key="href")[0].split('/')[-1], repo_page=repo_page),
                              "topics": self.getRepoTopics(repository.get_attribute_list(key="href")[0].split('/')[-1], repo_page=repo_page),
                              "languages": self.getRepoLanguages(repository.get_attribute_list(key="href")[0].split('/')[-1], repo_page=repo_page)})
                repo = repos[-1]
                if verbose:
                    print()
                    display(' ', f"Repository     = {Back.MAGENTA}{repo['name']}{Back.RESET}")
                    display(':', f"Link           = {Back.MAGENTA}{repo['link']}{Back.RESET}")
                    if repo['about'] != None:
                        display(':', f"About          = {Back.MAGENTA}{repo['about']}{Back.RESET}")
                    display(':', f"Default Branch = {Back.MAGENTA}{repo['default_branch']}{Back.RESET}")
                    display(':', f"Commits        = {Back.MAGENTA}{repo['commits']}{Back.RESET}")
                    display(':', f"Stars          = {Back.MAGENTA}{len(repo['star_users'])}{Back.RESET}")
                    display(':', f"Watchers       = {Back.MAGENTA}{len(repo['watchers'])}{Back.RESET}")
                    display(':', f"Forks          = {Back.MAGENTA}{repo['forks']}{Back.RESET}")
                    if len(repo['languages']) != 0:
                        display('+', "Languages")
                        for langauge in repo["languages"]:
                            display(':', f"\t* {langauge['percentage']}% => {Back.MAGENTA}{langauge['name']}{Back.RESET}")
                    if len(repo['topics']) != 0:
                        display('+', "Topics")
                        for topic in repo["topics"]:
                            display(':', f"\t* {topic['name']} ({Back.MAGENTA}{topic['link']}{Back.RESET})")
        if verbose:
            print()
        return repos
    def getFollowers(self):
        page_number, followers = 1, []
        followers_page_link = f"{self.home_page_link}/{Github.followers}&{Github.page}{page_number}"
        followers_page = requests.get(followers_page_link, headers=headers)
        followers_page_html = BeautifulSoup(followers_page.content, "html.parser")
        while True:
            follower_tags = followers_page_html.find_all("span", attrs={"class": "Link--secondary"})
            if len(follower_tags) == 0:
                break
            for follower_tag in follower_tags:
                followers.append(follower_tag.text)
            page_number += 1
            followers_page_link = f"{self.home_page_link}/{Github.followers}&{Github.page}{page_number}"
            followers_page = requests.get(followers_page_link, headers=headers)
            followers_page_html = BeautifulSoup(followers_page.content, "html.parser")
        return followers
    def getFollowing(self):
        page_number, following = 1, []
        following_page_link = f"{self.home_page_link}/{Github.following}&{Github.page}{page_number}"
        following_page = requests.get(following_page_link, headers=headers)
        following_page_html = BeautifulSoup(following_page.content, "html.parser")
        while True:
            follower_tags = following_page_html.find_all("span", attrs={"class": "Link--secondary"})
            if len(follower_tags) == 0:
                break
            for follower_tag in follower_tags:
                following.append(follower_tag.text)
            page_number += 1
            following_page_link = f"{self.home_page_link}/{Github.following}&{Github.page}{page_number}"
            following_page = requests.get(following_page_link, headers=headers)
            following_page_html = BeautifulSoup(following_page.content, "html.parser")
        return following
    def getStarRepos(self):
        starRepos = []
        next_link = f"{self.home_page_link}{Github.stars}"
        while next_link != None:
            star_page = requests.get(next_link, headers=headers)
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
            name_info["Name"] = name.text.strip()
        if nickname != None:
            name_info["Nickname"] = nickname.text.strip()
        if pronouns != None:
            name_info["Pronouns"] = pronouns.text.strip()
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
        achievement_page = requests.get(achievement_page_link, headers=headers)
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
    def getRepoDefaultBranch(self, repo, repo_page=None):
        if repo_page == None:
            repo_link = f"{self.home_page_link}/{repo}"
            repo_page = requests.get(repo_link, headers=headers)
        if repo_page.status_code != 200:
            return None
        repo_html = BeautifulSoup(repo_page.content, "html.parser")
        branch_tag = repo_html.find("summary", attrs={"title": "Switch branches or tags"})
        try:
            return branch_tag.text.strip()
        except:
            return None
    def getRepoBranchCount(self, repo, repo_page=None):
        if repo_page == None:
            repo_link = f"{self.home_page_link}/{repo}"
            repo_page = requests.get(repo_link, headers=headers)
        if repo_page.status_code != 200:
            return None
        repo_html = BeautifulSoup(repo_page.content, "html.parser")
        try:
            branch_count_tag = repo_html.find_all("a", attrs={"href": f"/{self.id}/{repo}/branches"})[-1]
            return int(branch_count_tag.text.strip().split('\n')[0])
        except:
            return 0
    def getRepoStarCount(self, repo):
        repo_link = f"{self.home_page_link}/{repo}"
        repo_page = requests.get(repo_link, headers=headers)
        if repo_page.status_code != 200:
            return None
        repo_html = BeautifulSoup(repo_page.content, "html.parser")
        star_tag = repo_html.find_all("a", attrs={"href": f"/{self.id}/{repo}/stargazers"})[-1]
        return int(star_tag.text.strip().split('\n')[0])
    def getRepoWatcherCount(self, repo):
        repo_link = f"{self.home_page_link}/{repo}"
        repo_page = requests.get(repo_link, headers=headers)
        if repo_page.status_code != 200:
            return None
        repo_html = BeautifulSoup(repo_page.content, "html.parser")
        star_tag = repo_html.find_all("a", attrs={"href": f"/{self.id}/{repo}/watchers"})[-1]
        return int(star_tag.text.strip().split('\n')[0])
    def getRepoCommitCount(self, repo, repo_page=None):
        if repo_page == None:
            repo_link = f"{self.home_page_link}/{repo}"
            repo_page = requests.get(repo_link, headers=headers)
        if repo_page.status_code != 200:
            return None
        repo_html = BeautifulSoup(repo_page.content, "html.parser")
        try:
            star_tag = repo_html.find_all("a", attrs={"href": f"/{self.id}/{repo}/commits/{self.getRepoDefaultBranch(repo, repo_page=repo_page)}"})[-1]
            return int(star_tag.text.strip().split('\n')[0])
        except:
            return 0
    def getRepoForkCount(self, repo, repo_page=None):
        if repo_page == None:
            repo_link = f"{self.home_page_link}/{repo}"
            repo_page = requests.get(repo_link, headers=headers)
        if repo_page.status_code != 200:
            return None
        repo_html = BeautifulSoup(repo_page.content, "html.parser")
        try:
            star_tag = repo_html.find_all("a", attrs={"href": f"/{self.id}/{repo}/forks"})[-1]
            return int(star_tag.text.strip().split('\n')[0])
        except:
            return 0
    def getRepoStarUsers(self, repo):
        users = []
        repo_link = f"{self.home_page_link}/{repo}/stargazers"
        repo_page = requests.get(repo_link, headers=headers)
        if repo_page.status_code != 200:
            return None
        repo_html = BeautifulSoup(repo_page.content, "html.parser")
        user_tags = repo_html.find_all("a", attrs={"data-hovercard-type": "user"})
        for user_tag in user_tags:
            if user_tag.get_attribute_list(key="rel")[0] == "author" or user_tag.text.strip() == '':
                continue
            users.append(user_tag.text.strip())
        if "Cookie" in headers.keys():
            users = users[1:]
        return users
    def getRepoWatchers(self, repo):
        users = []
        repo_link = f"{self.home_page_link}/{repo}/watchers"
        repo_page = requests.get(repo_link, headers=headers)
        if repo_page.status_code != 200:
            return None
        repo_html = BeautifulSoup(repo_page.content, "html.parser")
        user_tags = repo_html.find_all("a", attrs={"data-hovercard-type": "user"})
        for user_tag in user_tags:
            if user_tag.get_attribute_list(key="rel")[0] == "author" or user_tag.text.strip() == '':
                continue
            users.append(user_tag.text.strip())
        if "Cookie" in headers.keys():
            users = users[1:]
        return users
    def getRepoTopics(self, repo, repo_page=None):
        topics = []
        if repo_page == None:
            repo_link = f"{self.home_page_link}/{repo}"
            repo_page = requests.get(repo_link, headers=headers)
        if repo_page.status_code != 200:
            return None
        repo_html = BeautifulSoup(repo_page.content, "html.parser")
        topic_tags = repo_html.find_all("a", attrs={"class": "topic-tag"})
        for topic_tag in topic_tags:
            topics.append({"name": topic_tag.text.strip(), "link": f"{Github.github[:-1]}{topic_tag.get_attribute_list(key='href')[0]}"})
        return topics
    def getRepoAbout(self, repo, repo_page=None):
        if repo_page == None:
            repo_link = f"{self.home_page_link}/{repo}"
            repo_page = requests.get(repo_link, headers=headers)
        if repo_page.status_code != 200:
            return None
        repo_html = BeautifulSoup(repo_page.content, "html.parser")
        h2_tags = repo_html.find_all("h2")
        for h2_tag in h2_tags:
            if h2_tag.text == "About":
                about_tag = list(h2_tag.parents)[0].find("p")
                try:
                    return about_tag.text.strip()
                except AttributeError:
                    return None
    def getRepoLanguages(self, repo, repo_page=None):
        languages = []
        if repo_page == None:
            repo_link = f"{self.home_page_link}/{repo}"
            repo_page = requests.get(repo_link, headers=headers)
        if repo_page.status_code != 200:
            return None
        repo_html = BeautifulSoup(repo_page.content, "html.parser")
        h2_tags = repo_html.find_all("h2")
        for h2_tag in h2_tags:
            if h2_tag.text == "Languages":
                languange_tags = list(h2_tag.parents)[0].find_all("a")
                break
        else:
            return []
        for language_tag in languange_tags:
            language = language_tag.text.strip().split('\n')
            languages.append({"name": language[0], "percentage": float(language[1][:-1])})
        return languages
    def getContributionCalendar(self):
        contribution_calendar = []
        year_tags = self.home_page_html.find_all("a", attrs={"class": "js-year-link"})
        for year_tag in year_tags:
            link = f"{Github.github[:-1]}{year_tag.get_attribute_list(key='href')[0]}"
            page = requests.get(link, headers=headers)
            html = BeautifulSoup(page.content, "html.parser")
            rect_tags = html.find_all("span", attrs={"class": "sr-only"})
            for rect_tag in rect_tags:
                if rect_tag.text != "":
                    contribution = rect_tag.text.split(' ')
                    contribution_data = {}
                    if contribution[0] == "No":
                        contribution_data["contributions"] = 0
                    else:
                        try:
                            contribution_data["contributions"] = int(contribution[0])
                        except:
                            continue
                    contribution_data["month"] = contribution[3]
                    contribution_data["date"] = contribution[4][:-1]
                    contribution_data["year"] = year_tag.text
                    contribution_data["day"] = datetime(int(contribution_data["year"]), int(month_indexes[contribution_data["month"]]), int(contribution_data["date"][:-2])).strftime("%A")
                    contribution_calendar.append(contribution_data)
        return contribution_calendar
    def dumpRepo(self, repo):
        cwd = Path.cwd()
        user_folder = cwd / "users" / self.id / "repositories"
        user_folder.mkdir(exist_ok=True, parents=True)
        os.chdir(str(user_folder))
        run(["git", "clone", f"{self.home_page_link}/{repo}.git"])
        os.chdir(cwd)

def read(fileName):
    try:
        with open(f"data/{fileName}", 'rb') as file:
            users_data = load(file)
    except FileNotFoundError:
        display('-', f"File {Back.MAGENTA}{fileName}{Back.RESET} not found!")
        return
    except:
        display('-', f"Error while reading File {Back.MAGENTA}{fileName}{Back.RESET}")
        return
    for user in users_data:
        for name_type, name in users_data[user]["names"].items():
            if name != '':
                display(':', f"{name_type}:\t{Back.MAGENTA}{name}{Back.RESET}")
        if users_data[user]["pro"]:
            display(':', f"User has a {Back.MAGENTA}PRO{Back.RESET} Account")
        if users_data[user]["mail"] != None:
            display(':', f"Mail = {Back.MAGENTA}{users_data[user]['mail']}{Back.RESET}")
        if users_data[user]["location"] != None:
            display(':', f"Location = {Back.MAGENTA}{users_data[user]['location']}{Back.RESET}")
        if users_data[user]["timezone"] != None:
            display(':', f"Time Zone = {Back.MAGENTA}{users_data[user]['timezone']}{Back.RESET}")
        if len(users_data[user]["organization"]) != 0:
            display('+', f"Organizations")
            for organization in users_data[user]["organization"]:
                if "link" in organization.keys():
                    display(':', f"\t* {organization['name']}({Back.MAGENTA}{organization['link']}{Back.RESET})")
                else:
                    display(':', f"\t* {organization['name']}")
        if users_data[user]["workplace"] != None:
            display(':', f"Workplace = {Back.MAGENTA}{users_data[user]['workplace']}{Back.RESET}")
        if len(users_data[user]["links"]) != 0:
            display('+', "Links")
            for link in users_data[user]["links"]:
                display(':', f"\t{link['name']}:\t{Back.MAGENTA}{link['link']}{Back.RESET}")
        if users_data[user]["status"] != None:
            display(':', f"Status = {Back.MAGENTA}{users_data[user]['status']}{Back.RESET}")
        if users_data[user]["bio"] != None and users_data[user]["bio"] != '':
            display(':', f"Bio: {users_data[user]['bio']}")
        if len(users_data[user]["achievements"]) != 0:
            display('+', f"Achievements")
            for achievement in users_data[user]["achievements"]:
                display(':', f"\t{Back.MAGENTA}{achievement['name']}{Back.RESET}: {achievement['count']}")
        if len(users_data[user]["followers"]) != 0:
            display('+', "Followers")
            for follower in users_data[user]["followers"]:
                display(':', f"\t* {follower} ({Back.MAGENTA}{Github.github}{follower}{Back.RESET})")
        if len(users_data[user]["following"]) != 0:
            display('+', "Following")
            for following in users_data[user]["following"]:
                display(':', f"\t* {following} ({Back.MAGENTA}{Github.github}{following}{Back.RESET})")
        repos = users_data[user]["repos"]
        for repo in repos:
            display(' ', f"Repository     = {Back.MAGENTA}{repo['name']}{Back.RESET}")
            display(':', f"Link           = {Back.MAGENTA}{repo['link']}{Back.RESET}")
            if repo['about'] != None:
                display(':', f"About          = {Back.MAGENTA}{repo['about']}{Back.RESET}")
            display(':', f"Default Branch = {Back.MAGENTA}{repo['default_branch']}{Back.RESET}")
            display(':', f"Commits        = {Back.MAGENTA}{repo['commits']}{Back.RESET}")
            display(':', f"Stars          = {Back.MAGENTA}{len(repo['star_users'])}{Back.RESET}")
            display(':', f"Watchers       = {Back.MAGENTA}{len(repo['watchers'])}{Back.RESET}")
            display(':', f"Forks          = {Back.MAGENTA}{repo['forks']}{Back.RESET}")
            if len(repo['languages']) != 0:
                display('+', "Languages")
                for langauge in repo["languages"]:
                    display(':', f"\t* {langauge['percentage']}% => {Back.MAGENTA}{langauge['name']}{Back.RESET}")
            if len(repo['topics']) != 0:
                display('+', "Topics")
                for topic in repo["topics"]:
                    display(':', f"\t* {topic['name']} ({Back.MAGENTA}{topic['link']}{Back.RESET})")
        display(':', f"Total Repositories = {Back.MAGENTA}{len(users_data[user]['repos'])}{Back.RESET}")
        if len(users_data[user]["starred_repos"]) != 0:
            display('+', "Starred Repositories")
            for starred_repo in users_data[user]["starred_repos"]:
                display(':', f"\t* {starred_repo['name']} ({Back.MAGENTA}{starred_repo['link']}{Back.RESET})")
        print()
        repo_major_languages = {}
        languages = {}
        total_repo_major_languages = 0
        total_languages = 0
        for repo in users_data[user]["repos"]:
            if len(repo["languages"]) > 0:
                if repo["languages"][0]["name"] not in repo_major_languages.keys():
                    repo_major_languages[repo["languages"][0]["name"]] = 0
                repo_major_languages[repo["languages"][0]["name"]] += 1
                total_repo_major_languages += 1
            for language in repo["languages"]:
                if language["name"] not in languages.keys():
                    languages[language["name"]] = 0
                languages[language["name"]] += 1
                total_languages += 1
        repo_major_languages = dict(list(reversed(sorted(repo_major_languages.items(), key=lambda major_language: major_language[1]))))
        langauges = dict(list(reversed(sorted(languages.items(), key=lambda language: language[1]))))
        if len(repo_major_languages) > 0:
            display('+', "Major Language of Repositories")
            for repo_major_langauge, count in repo_major_languages.items():
                display(':', f"\t* {repo_major_langauge}: {Back.MAGENTA}{count} ({count/total_repo_major_languages*100:.2f}%){Back.RESET}")
        if len(languages) > 0:
            display('+', "Language used by User")
            for language, count in languages.items():
                display(':', f"\t* {language}: {Back.MAGENTA}{count} ({count/total_languages*100:.2f}%){Back.RESET}")
        print()
        working_days = {"Monday": 0, "Tuesday": 0, "Wednesday": 0, "Thursday": 0, "Friday": 0, "Saturday": 0, "Sunday": 0}
        contributions = {"Monday": 0, "Tuesday": 0, "Wednesday": 0, "Thursday": 0, "Friday": 0, "Saturday": 0, "Sunday": 0}
        total_working_days = 0
        total_contributions = 0
        for contribution in users_data[user]["contribution_calendar"]:
            contributions[contribution["day"]] += contribution["contributions"]
            total_contributions += contribution["contributions"]
            if contribution["contributions"] > 0:
                working_days[contribution["day"]] += 1
                total_working_days += 1
        working_days = dict(list(reversed((sorted(working_days.items(), key=lambda working_day: working_day[1])))))
        contributions = dict(list(reversed(sorted(contributions.items(), key=lambda contribution: contribution[1]))))
        if total_working_days == 0 or total_contributions == 0:
            continue
        display('+', "Working Days")
        for working_day, day_count in working_days.items():
            display(':', f"\t* {working_day}: {Back.MAGENTA}{day_count} ({day_count/total_working_days*100:.2f}%){Back.RESET}")
        display('*', f"Total Working Days = {Back.MAGENTA}{total_working_days}{Back.RESET}")
        display('+', "Contributions")
        for contribution_day, contribution_count in contributions.items():
            display(':', f"\t* {contribution_day}: {Back.MAGENTA}{contribution_count} ({contribution_count/total_contributions*100:.2f}%){Back.RESET}")
        display('*', f"Total Contributions = {Back.MAGENTA}{total_contributions}{Back.RESET}")
        print()

if __name__ == "__main__":
    data = get_arguments(('-u', "--users", "users", "ID of the Users to get Details. (seperated by ',')"),
                         ('-l', "--load", "load", "File from which to load the Users"),
                         ('-w', "--write", "write", "Name of the file to dump extracted data"),
                         ('-r', "--read", "read", "Read a dump file"),
                         ('-c', "--clone-repositories", "clone_repos", "Clone All Repositories of a User (True/False)"),
                         ('-s', "--session-id", "session_id", "Session-ID (Cookie) for Request Header (If Log-In)"))
    if data.read:
        read(data.read)
        exit(0)
    if not data.users:
        if not data.load:
            display('-', f"Please Enter the {Back.MAGENTA}ID{Back.RESET} of the Users")
            exit(0)
        else:
            try:
                with open(data.load, 'r') as file:
                    data.users = [user for user in file.read().split('\n') if user != '']
            except FileNotFoundError:
                display('-', f"File {Back.MAGENTA}{data.load}{Back.RESET} not found!")
                exit(0)
    else:
        data.users = data.users.split(',')
    if data.session_id:
        display(':', "Setting Session-ID")
        headers["Cookie"] = data.session_id
    users_data = {}
    for user in data.users:
        print()
        github_user = Github(user)
        if github_user.home_page.status_code != 200:
            display('-', f"{Back.MAGENTA}{user}{Back.RESET} not found")
            continue
        users_data[user] = {}
        users_data[user]["names"] = github_user.VCardNames()
        for name_type, name in users_data[user]["names"].items():
            if name != '':
                display(':', f"{name_type}:\t{Back.MAGENTA}{name}{Back.RESET}")
        users_data[user]["pro"] = github_user.isPro()
        if users_data[user]["pro"]:
            display(':', f"User has a {Back.MAGENTA}PRO{Back.RESET} Account")
        users_data[user]["mail"] = github_user.getMail()
        if users_data[user]["mail"] != None:
            display(':', f"Mail = {Back.MAGENTA}{users_data[user]['mail']}{Back.RESET}")
        users_data[user]["location"] = github_user.getLocation()
        if users_data[user]["location"] != None:
            display(':', f"Location = {Back.MAGENTA}{users_data[user]['location']}{Back.RESET}")
        users_data[user]["timezone"] = github_user.getLocalTimeZone()
        if users_data[user]["timezone"] != None:
            display(':', f"Time Zone = {Back.MAGENTA}{users_data[user]['timezone']}{Back.RESET}")
        users_data[user]["organization"] = github_user.getOrganization()
        if len(users_data[user]["organization"]) != 0:
            display('+', f"Organizations")
            for organization in users_data[user]["organization"]:
                if "link" in organization.keys():
                    display(':', f"\t* {organization['name']}({Back.MAGENTA}{organization['link']}{Back.RESET})")
                else:
                    display(':', f"\t* {organization['name']}")
        users_data[user]["workplace"] = github_user.getWorkPlace()
        if users_data[user]["workplace"] != None:
            display(':', f"Workplace = {Back.MAGENTA}{users_data[user]['workplace']}{Back.RESET}")
        users_data[user]["links"] = github_user.getLinks()
        if len(users_data[user]["links"]) != 0:
            display('+', "Links")
            for link in users_data[user]["links"]:
                display(':', f"\t{link['name']}:\t{Back.MAGENTA}{link['link']}{Back.RESET}")
        users_data[user]["status"] = github_user.getStatus()
        if users_data[user]["status"] != None:
            display(':', f"Status = {Back.MAGENTA}{users_data[user]['status']}{Back.RESET}")
        users_data[user]["bio"] = github_user.getBio()
        if users_data[user]["bio"] != None and users_data[user]["bio"] != '':
            display(':', f"Bio: {users_data[user]['bio']}")
        users_data[user]["achievements"] = github_user.getAchievements()
        if len(users_data[user]["achievements"]) != 0:
            display('+', f"Achievements")
            for achievement in users_data[user]["achievements"]:
                display(':', f"\t{Back.MAGENTA}{achievement['name']}{Back.RESET}: {achievement['count']}")
        users_data[user]["followers"] = github_user.getFollowers()
        if len(users_data[user]["followers"]) != 0:
            display('+', "Followers")
            for follower in users_data[user]["followers"]:
                display(':', f"\t* {follower} ({Back.MAGENTA}{Github.github}{follower}{Back.RESET})")
        users_data[user]["following"] = github_user.getFollowing()
        if len(users_data[user]["following"]) != 0:
            display('+', "Following")
            for following in users_data[user]["following"]:
                display(':', f"\t* {following} ({Back.MAGENTA}{Github.github}{following}{Back.RESET})")
        display(':', "Fetching Repository Data...", start='\n')
        users_data[user]["repos"] = github_user.getRepos(verbose=True)
        display('+', "Gathered Repository Data")
        display(':', f"Total Repositories = {Back.MAGENTA}{len(users_data[user]['repos'])}{Back.RESET}")
        users_data[user]["starred_repos"] = github_user.getStarRepos()
        if len(users_data[user]["starred_repos"]) != 0:
            display('+', "Starred Repositories")
            for starred_repo in users_data[user]["starred_repos"]:
                display(':', f"\t* {starred_repo['name']} ({Back.MAGENTA}{starred_repo['link']}{Back.RESET})")
        print()
        repo_major_languages = {}
        languages = {}
        total_repo_major_languages = 0
        total_languages = 0
        for repo in users_data[user]["repos"]:
            if len(repo["languages"]) > 0:
                if repo["languages"][0]["name"] not in repo_major_languages.keys():
                    repo_major_languages[repo["languages"][0]["name"]] = 0
                repo_major_languages[repo["languages"][0]["name"]] += 1
                total_repo_major_languages += 1
            for language in repo["languages"]:
                if language["name"] not in languages.keys():
                    languages[language["name"]] = 0
                languages[language["name"]] += 1
                total_languages += 1
        repo_major_languages = dict(list(reversed(sorted(repo_major_languages.items(), key=lambda major_language: major_language[1]))))
        langauges = dict(list(reversed(sorted(languages.items(), key=lambda language: language[1]))))
        if len(repo_major_languages) > 0:
            display('+', "Major Language of Repositories")
            for repo_major_langauge, count in repo_major_languages.items():
                display(':', f"\t* {repo_major_langauge}: {Back.MAGENTA}{count} ({count/total_repo_major_languages*100:.2f}%){Back.RESET}")
        if len(languages) > 0:
            display('+', "Language used by User")
            for language, count in languages.items():
                display(':', f"\t* {language}: {Back.MAGENTA}{count} ({count/total_languages*100:.2f}%){Back.RESET}")
        print()
        users_data[user]["contribution_calendar"] = github_user.getContributionCalendar()
        working_days = {"Monday": 0, "Tuesday": 0, "Wednesday": 0, "Thursday": 0, "Friday": 0, "Saturday": 0, "Sunday": 0}
        contributions = {"Monday": 0, "Tuesday": 0, "Wednesday": 0, "Thursday": 0, "Friday": 0, "Saturday": 0, "Sunday": 0}
        total_working_days = 0
        total_contributions = 0
        for contribution in users_data[user]["contribution_calendar"]:
            contributions[contribution["day"]] += contribution["contributions"]
            total_contributions += contribution["contributions"]
            if contribution["contributions"] > 0:
                working_days[contribution["day"]] += 1
                total_working_days += 1
        working_days = dict(list(reversed((sorted(working_days.items(), key=lambda working_day: working_day[1])))))
        contributions = dict(list(reversed(sorted(contributions.items(), key=lambda contribution: contribution[1]))))
        if total_working_days == 0 or total_contributions == 0:
            continue
        display('+', "Working Days")
        for working_day, day_count in working_days.items():
            display(':', f"\t* {working_day}: {Back.MAGENTA}{day_count} ({day_count/total_working_days*100:.2f}%){Back.RESET}")
        display('*', f"Total Working Days = {Back.MAGENTA}{total_working_days}{Back.RESET}")
        display('+', "Contributions")
        for contribution_day, contribution_count in contributions.items():
            display(':', f"\t* {contribution_day}: {Back.MAGENTA}{contribution_count} ({contribution_count/total_contributions*100:.2f}%){Back.RESET}")
        display('*', f"Total Contributions = {Back.MAGENTA}{total_contributions}{Back.RESET}")
        print()
        if data.clone_repos == "True":
            display(':', f"Cloning {Back.MAGENTA}{len(users_data[user]['repos'])}{Back.RESET} Repositories")
            for repo in users_data[user]["repos"]:
                github_user.dumpRepo(repo["name"])
    if data.write:
        cwd = Path.cwd()
        data_folder = cwd / "data"
        data_folder.mkdir(exist_ok=True)
        display(':', f"Dumping Data in File = {str(data_folder)}/{data.write}")
        with open(f"data/{data.write}", 'wb') as file:
            dump(users_data, file)
        display('+', f"Dumped Data in File = {str(data_folder)}/{data.write}")
