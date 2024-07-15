from dataclasses import dataclass
from typing import List, Union, Optional
import sys
import asyncio
import aiohttp
from bs4 import BeautifulSoup
import json
import datetime

@dataclass
class Link:
    url : Optional[str]
    title : Optional[str]

@dataclass
class Contact:
    url : Optional[str]
    title : Optional[str]
    
@dataclass
class LinktreeUser:
    username : str
    url : Optional[str]
    avartar_image : Optional[str]
    id : int
    isActive : bool
    description : Optional[str]
    createdAt: int
    updatedAt: int
    links : List[Link]
    contacts : List[Contact]

class Linktree(object):
    async def _fetch(self, url : str,
                     method : str = "GET", 
                     headers : dict = {}, 
                     data : dict = {}) -> tuple[aiohttp.ClientSession, aiohttp.ClientSession]:
        
        session = aiohttp.ClientSession(headers= headers)
        resp = await session.request(method = method ,url = url, json = data)
        return session, resp
                    
    async def getSource(self, url : str):
        session, resp = await self._fetch(url)
        content = await resp.text()
        await session.close()
        return content
            
    async def getUserInfoJSON(self, source = None,  url : Optional[str] = None, username : Optional[str] = None):            
        if url is None and username:
            url = f"https://linktr.ee/{username}"

        if source is None and url:
            source = await self.getSource(url)

        soup = BeautifulSoup(source, 'html.parser')
        attributes = {"id":"__NEXT_DATA__"}
        user_info = soup.find('script', attrs=attributes)
        user_data = json.loads(user_info.contents[0])["props"]["pageProps"]
        return user_data

    async def uncensorLinks(self, account_id : int, link_ids : Union[List[int], int]):
        if isinstance(link_ids, int):
            link_ids = [link_ids]
        
        headers = {"origin": "https://linktr.ee",
                   "referer": "https://linktr.ee",
                   "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"}
        
        data = {"accountId": account_id, 
                "validationInput": {"acceptedSensitiveContent": link_ids},
                "requestSource": {"referrer":None}}
        
        url = "https://linktr.ee/api/profiles/validation/gates"
        session, resp = await self._fetch(method = "POST", url = url, headers = headers, data= data)
        
        json_resp = await resp.json()
        await session.close()
        
        _links = json_resp["links"]
        
        links = []
        for _link in _links:
            url = _link["url"]
            link = Link(url = url)
            links.append(link)
        return links
    
    async def getUserLinks(self, username : Optional[str] = None, data : Optional[dict] = None):
        if data is None and username:
            data = await self.getUserInfoJSON(username= username)
            
        user_id = data["account"]["id"]
        _links = data["links"]
    
        links = []
        censored_links_ids = []
        
        for _link in _links:
            id = int(_link["id"])
            url = _link["url"]
            locked = _link["locked"]
            title = _link["title"]

            link = Link(url = url, title = title)
            if _link["type"] == "COMMERCE_PAY":
                continue

            if _link["type"] == "HEADER":
                continue
            
            if url is None and locked is True:
                censored_links_ids.append(id)
                continue
            links.append(link)

        uncensored_links = await self.uncensorLinks(account_id= user_id, 
                                                    link_ids= censored_links_ids)
        links.extend(uncensored_links)
        
        return links
    
    async def getUserContacts(self, username: Optional[str] = None, data : Optional[dict] = None):
        if data is None and username:
            data = await self.getUserInfoJSON(username= username)

        _contacts = data["socialLinks"]
    
        contacts = []        
        
        for _contact in _contacts:
            url = _contact["url"]
            title = _contact["type"]

            contact = Contact(url = url, title = title)
            
            contacts.append(contact)

        return contacts

    async def getLinktreeUserInfo(self, url : Optional[str] = None, username : Optional[str] = None)-> LinktreeUser:
        if url is None and username is None:
            print("Please pass linktree username or url.")
            return

        JSON_INFO = await self.getUserInfoJSON(url = url, username= username)
        account = JSON_INFO["account"]
        username = account["username"]
        avatar_image = account["profilePictureUrl"]
        url = f"https://linktr.ee/{username}" if url is None else url 
        id = account["id"]
        isActive = account["isActive"]
        createdAt = account["createdAt"]
        updatedAt = account["updatedAt"]
        description = account["description"]

        links = await self.getUserLinks(data= JSON_INFO)
        contacts = await self.getUserContacts(data= JSON_INFO)
        
        return LinktreeUser(username = username,
                            url = url,
                            avartar_image= avatar_image,
                            id = id,
                            isActive = isActive,
                            createdAt = createdAt,
                            updatedAt = updatedAt,
                            description = description,
                            links = links,
                            contacts = contacts)

def convert_unix_time(t):
    t = t/1000
    date_time = datetime.datetime.fromtimestamp(t)
    return date_time


async def main():
    # url = "https://linktr.ee/cktc"
    
    if len(sys.argv) < 2:
        print("Username or url is needed!")
        sys.exit(1)

    input = sys.argv[1]
    if "linktr.ee" in input:
        username, url = None, input
    else:
        username, url = input, None

    linktree = Linktree()
    user_info = await linktree.getLinktreeUserInfo(username = username, 
                                                    url= url)

    print(f"username : {user_info.username}")
    print(f"avatar image: {user_info.avartar_image}")
    print(f"isActive : {user_info.isActive}")
    print(f"descripition : {user_info.description}")
    print(f"createdAt unix : {user_info.createdAt}")
    print(f"updatedAt unix : {user_info.updatedAt}")
    print(f"createdAt : {str(convert_unix_time(user_info.createdAt))}")
    print(f"updatedAt : {str(convert_unix_time(user_info.updatedAt))}")

    print("\nLinks:")
    for link in user_info.links:
        print(link.title + ": "+ link.url)

    print("\nContacts:")
    for contact in user_info.contacts:
        print(contact.title + ": "+ contact.url)

    result = {
        "username" : user_info.username,
        "avatar": user_info.avartar_image,
        "isActive": user_info.isActive,
        "description": user_info.description,
        "createdAt unix": user_info.createdAt,
        "udpatedAt unix": user_info.updatedAt,
        "createdAt": str(convert_unix_time(user_info.createdAt)),
        "udpatedAt": str(convert_unix_time(user_info.updatedAt)),
        "links": [{link.title: link.url} for link in user_info.links],
        "contacts": [{contact.title: contact.url} for contact in user_info.contacts],
    }

    with open(f"./output/linktree_{user_info.username}.json", "w") as output:
        json.dump(result, output, indent=4)
        
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())