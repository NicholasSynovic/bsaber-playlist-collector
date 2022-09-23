from concurrent.futures import ThreadPoolExecutor
from os import mkdir
from urllib.parse import urlparse

from bs4 import BeautifulSoup, ResultSet, Tag
from progress.bar import Bar
from progress.spinner import Spinner
from requests import Response, get

updateOfficialPlaylistURL = (
    lambda page: f"https://bsaber.com/category/official-playlists/page/{page}"
)
updateCommunityPlaylistURL = (
    lambda page: f"https://bsaber.com/category/community-playlists/page/{page}"
)


def getHTML(url: str) -> BeautifulSoup | bool:
    resp: Response = get(url)
    if resp.status_code == 404:
        return False
    return BeautifulSoup(markup=resp.content, features="lxml")


def scrapeForOfficialPlaylists() -> list:
    icon: Tag
    data: BeautifulSoup | bool = True
    pageCounter: int = 1

    playlists: list = []

    with Spinner(
        "Getting a list of all official playlist URLs on bsaber.com..."
    ) as spinner:
        while True:
            url: str = updateOfficialPlaylistURL(pageCounter)
            data = getHTML(url)

            if data == False:
                pageCounter -= 1
                spinner.message = (
                    f"Found {pageCounter} official playlists pages on bsaber.com"
                )
                spinner.update()
                break

            downloadIcons: ResultSet = data.find_all(
                name="a", attrs={"class": "action post-icon bsaber-tooltip -beatmods"}
            )
            for icon in downloadIcons:
                playlists.append(icon.get("href").replace("bsplaylist://playlist/", ""))
            pageCounter += 1
            spinner.next()
    return playlists


def scrapeForCommunityPlaylists() -> list:
    icon: Tag
    data: BeautifulSoup | bool = True
    pageCounter: int = 1

    playlists: list = []

    with Spinner(
        "Getting a list of all community playlist URLs on bsaber.com..."
    ) as spinner:
        while True:
            url: str = updateCommunityPlaylistURL(pageCounter)
            data = getHTML(url)

            if data == False:
                pageCounter -= 1
                spinner.message = (
                    f"Found {pageCounter} community playlists pages on bsaber.com"
                )
                spinner.update()
                break

            downloadIcons: ResultSet = data.find_all(
                name="a", attrs={"class": "action post-icon bsaber-tooltip -beatmods"}
            )
            for icon in downloadIcons:
                playlists.append(icon.get("href").replace("bsplaylist://playlist/", ""))
            pageCounter += 1
            spinner.next()
        return playlists


def downloadPlaylists(urls: set) -> None:
    try:
        mkdir("playlists")
    except OSError:
        pass

    with Bar("Downloading playlists...", max=len(urls)) as bar:

        def _download(url: str) -> None:
            filename: str = urlparse(url).path.split("/")[-1]
            content: bytes = get(url).content

            with open(f"playlists/{filename}", "wb") as file:
                file.write(content)
                file.close()
            bar.next()

        with ThreadPoolExecutor() as executor:
            executor.map(_download, urls)


def main() -> None:
    officialPlaylists: list = scrapeForOfficialPlaylists()
    communityPlaylists: list = scrapeForCommunityPlaylists()

    with open("officialPlaylists.txt", "w") as file:
        temp: list = [f"{url}\n" for url in officialPlaylists]
        file.writelines(temp)
        file.close()

    with open("communityPlaylists.txt", "w") as file:
        temp: list = [f"{url}\n" for url in communityPlaylists]
        file.writelines(temp)
        file.close()

    mergeList: list = officialPlaylists + communityPlaylists

    mergeSet: set = set(mergeList)
    downloadPlaylists(mergeSet)


if __name__ == "__main__":
    main()
