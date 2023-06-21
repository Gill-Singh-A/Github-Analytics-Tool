#! /usr/bin/env python3

import requests, os
from pathlib import Path
from datetime import date
from subprocess import run
from optparse import OptionParser
from bs4 import BeautifulSoup
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

def display(status, data, start='', end='\n'):
    print(f"{start}{status_color[status]}[{status}] {Fore.BLUE}[{date.today()} {strftime('%H:%M:%S', localtime())}] {status_color[status]}{Style.BRIGHT}{data}{Fore.RESET}{Style.RESET_ALL}", end=end)

def get_arguments(*args):
    parser = OptionParser()
    for arg in args:
        parser.add_option(arg[0], arg[1], dest=arg[2], help=arg[3])
    return parser.parse_args()[0]

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
    def getRepos(self, verbose=False):
        repos = []
        while len(repos) != self.repoCount:
            repo_page_link = f"{self.home_page_link}/{Github.repoTab}&{Github.page}{len(repos)//30+1}"
            repo_page = requests.get(repo_page_link)
            repo_page_html = BeautifulSoup(repo_page.content, "html.parser")
            repositories = repo_page_html.find_all(itemprop="name codeRepository")
            for repository in repositories:
                repos.append({"name": repository.get_attribute_list(key="href")[0].split('/')[-1],
                              "link": f"{self.home_page_link}/{repository.get_attribute_list(key='href')[0].split('/')[-1]}",
                              "default_branch": self.getRepoDefaultBranch(repository.get_attribute_list(key="href")[0].split('/')[-1]),
                              "branch_count": self.getRepoBranchCount(repository.get_attribute_list(key="href")[0].split('/')[-1]),
                              "commits": self.getRepoCommitCount(repository.get_attribute_list(key="href")[0].split('/')[-1]),
                              "about": self.getRepoAbout(repository.get_attribute_list(key="href")[0].split('/')[-1]),
                              "star_users": self.getRepoStarUsers(repository.get_attribute_list(key="href")[0].split('/')[-1]),
                              "watchers": self.getRepoWatchers(repository.get_attribute_list(key="href")[0].split('/')[-1]),
                              "forks": self.getRepoForkCount(repository.get_attribute_list(key="href")[0].split('/')[-1]),
                              "topics": self.getRepoTopics(repository.get_attribute_list(key="href")[0].split('/')[-1]),
                              "languages": self.getRepoLanguages(repository.get_attribute_list(key="href")[0].split('/')[-1])})
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
                            display(':', f"\t* {langauge['percentage']} => {Back.MAGENTA}{langauge['name']}{Back.RESET}")
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
    def getRepoDefaultBranch(self, repo):
        repo_link = f"{self.home_page_link}/{repo}"
        repo_page = requests.get(repo_link)
        if repo_page.status_code != 200:
            return None
        repo_html = BeautifulSoup(repo_page.content, "html.parser")
        branch_tag = repo_html.find("summary", attrs={"title": "Switch branches or tags"})
        return branch_tag.text.strip()
    def getRepoBranchCount(self, repo):
        repo_link = f"{self.home_page_link}/{repo}"
        repo_page = requests.get(repo_link)
        if repo_page.status_code != 200:
            return None
        repo_html = BeautifulSoup(repo_page.content, "html.parser")
        branch_count_tag = repo_html.find_all("a", attrs={"href": f"/{self.id}/{repo}/branches"})[-1]
        return int(branch_count_tag.text.strip().split('\n')[0])
    def getRepoStarCount(self, repo):
        repo_link = f"{self.home_page_link}/{repo}"
        repo_page = requests.get(repo_link)
        if repo_page.status_code != 200:
            return None
        repo_html = BeautifulSoup(repo_page.content, "html.parser")
        star_tag = repo_html.find_all("a", attrs={"href": f"/{self.id}/{repo}/stargazers"})[-1]
        return int(star_tag.text.strip().split('\n')[0])
    def getRepoWatcherCount(self, repo):
        repo_link = f"{self.home_page_link}/{repo}"
        repo_page = requests.get(repo_link)
        if repo_page.status_code != 200:
            return None
        repo_html = BeautifulSoup(repo_page.content, "html.parser")
        star_tag = repo_html.find_all("a", attrs={"href": f"/{self.id}/{repo}/watchers"})[-1]
        return int(star_tag.text.strip().split('\n')[0])
    def getRepoCommitCount(self, repo):
        repo_link = f"{self.home_page_link}/{repo}"
        repo_page = requests.get(repo_link)
        if repo_page.status_code != 200:
            return None
        repo_html = BeautifulSoup(repo_page.content, "html.parser")
        star_tag = repo_html.find_all("a", attrs={"href": f"/{self.id}/{repo}/commits/{self.getRepoDefaultBranch(repo)}"})[-1]
        return int(star_tag.text.strip().split('\n')[0])
    def getRepoForkCount(self, repo):
        repo_link = f"{self.home_page_link}/{repo}"
        repo_page = requests.get(repo_link)
        if repo_page.status_code != 200:
            return None
        repo_html = BeautifulSoup(repo_page.content, "html.parser")
        star_tag = repo_html.find_all("a", attrs={"href": f"/{self.id}/{repo}/forks"})[-1]
        return int(star_tag.text.strip().split('\n')[0])
    def getRepoStarUsers(self, repo):
        users = []
        repo_link = f"{self.home_page_link}/{repo}/stargazers"
        repo_page = requests.get(repo_link)
        if repo_page.status_code != 200:
            return None
        repo_html = BeautifulSoup(repo_page.content, "html.parser")
        user_tags = repo_html.find_all("a", attrs={"data-hovercard-type": "user"})
        for user_tag in user_tags:
            if user_tag.get_attribute_list(key="rel")[0] == "author" or user_tag.text.strip() == '':
                continue
            users.append(user_tag.text.strip())
        return users
    def getRepoWatchers(self, repo):
        users = []
        repo_link = f"{self.home_page_link}/{repo}/watchers"
        repo_page = requests.get(repo_link)
        if repo_page.status_code != 200:
            return None
        repo_html = BeautifulSoup(repo_page.content, "html.parser")
        user_tags = repo_html.find_all("a", attrs={"data-hovercard-type": "user"})
        for user_tag in user_tags:
            if user_tag.get_attribute_list(key="rel")[0] == "author" or user_tag.text.strip() == '':
                continue
            users.append(user_tag.text.strip())
        return users
    def getRepoTopics(self, repo):
        topics = []
        repo_link = f"{self.home_page_link}/{repo}"
        repo_page = requests.get(repo_link)
        if repo_page.status_code != 200:
            return None
        repo_html = BeautifulSoup(repo_page.content, "html.parser")
        topic_tags = repo_html.find_all("a", attrs={"class": "topic-tag"})
        for topic_tag in topic_tags:
            topics.append({"name": topic_tag.text.strip(), "link": f"{Github.github}{topic_tag.get_attribute_list(key='href')[0]}"})
        return topics
    def getRepoAbout(self, repo):
        repo_link = f"{self.home_page_link}/{repo}"
        repo_page = requests.get(repo_link)
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
    def getRepoLanguages(self, repo):
        languages = []
        repo_link = f"{self.home_page_link}/{repo}"
        repo_page = requests.get(repo_link)
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
            page = requests.get(link)
            html = BeautifulSoup(page.content, "html.parser")
            rect_tags = html.find_all("rect", attrs={"class": "ContributionCalendar-day"})
            for rect_tag in rect_tags:
                if rect_tag.text != "":
                    contribution = rect_tag.text.split(' ')
                    contribution_data = {}
                    if contribution[0] == "No":
                        contribution_data["contributions"] = 0
                    else:
                        contribution_data["contributions"] = int(contribution[0])
                    contribution_data["day"] = contribution[3]
                    contribution_data["month"] = contribution[4]
                    contribution_data["date"] = contribution[5]
                    contribution_data["year"] = contribution[6]
                    contribution_calendar.append(contribution_data)
        return contribution_calendar
    def dumpRepo(self, repo):
        cwd = Path.cwd()
        user_folder = cwd / "users" / self.id / "repositories"
        user_folder.mkdir(exist_ok=True, parents=True)
        os.chdir(str(user_folder))
        run(["git", "clone", f"{self.home_page_link}/{repo}.git"])
        os.chdir(cwd)

if __name__ == "__main__":
    data = get_arguments(('-u', "--users", "users", "ID of the Users to get Details. (seperated by ',')"),
                         ('-l', "--load", "load", "File from which to load the Users"),
                         ('-w', "--write", "write", "Name of the file to dump extracted data"),
                         ('-r', "--read", "read", "Read a dump file"),
                         ('-a', "--account", "account", "Account of a User to login to, for getting more Details"))
    if data.read:
        exit(0)
    if not data.users:
        if not data.load:
            display('-', f"Please Enter the {Back.MAGENTA}ID{Back.RESET} of the Users")
        else:
            try:
                with open(data.load, 'r') as file:
                    data.users = [user for user in file.read().split('\n') if user != '']
            except FileNotFoundError:
                display('-', f"File {Back.MAGENTA}{data.load}{Back.RESET} not found!")
                exit(0)
    else:
        data.users = data.users.split(',')
    users_data = {}
    for user in data.users:
        users_data[user] = {}
        github_user = Github(user)
        if github_user.home_page.status_code != 200:
            display('-', f"{Back.MAGENTA}{user}{Back.RESET} not found")
            continue
        users_data[user]["names"] = github_user.VCardNames()
        for name_type, name in users_data[user]["names"].items():
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
            display(':', f"Organization = {Back.MAGENTA}{users_data[user]['organization']}{Back.RESET}")
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
        display(':', "Fetching Repository Data...")
        users_data[user]["repos"] = github_user.getRepos(verbose=True)
        display('+', "Gathered Repository Data")
        display(':', f"Total Repositories = {Back.MAGENTA}{len(users_data[user]['repos'])}{Back.RESET}")
        users_data[user]["starred_repos"] = github_user.getStarRepos()
        if len(users_data[user]["starred_repos"]) != 0:
            display('+', "Starred Repositories")
            for starred_repo in users_data[user]["starred_repos"]:
                display(':', f"\t* {starred_repo['name']} ({Back.MAGENTA}{starred_repo['link']}{Back.RESET})")
        users_data[user]["contribution_calendar"] = github_user.getContributionCalendar()
        working_days = {"Monday": 0, "Tuesday": 0, "Wednesday": 0, "Thursday": 0, "Friday": 0, "Saturday": 0, "Sunday": 0}
        contributions = {"Monday": 0, "Tuesday": 0, "Wednesday": 0, "Thursday": 0, "Friday": 0, "Saturday": 0, "Sunday": 0}
    if data.write:
        cwd = Path.cwd()
        data_folder = cwd / "data"
        data_folder.mkdir(exist_ok=True)
        display(':', f"Dumping Data in File = {str(data_folder)}/{data.write}")
        with open(f"data/{data.write}", 'wb') as file:
            dump(users_data, file)
        display('+', f"Dumped Data in File = {str(data_folder)}/{data.write}")