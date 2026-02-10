from aiohttp import BasicAuth, ClientResponseError, ClientSession
from asyncio import run


async def main():
    auth = BasicAuth(login="ditto", password="Jtkx8L2XOCDD6XxU")

    ids = []
    cursor = ""
    async with ClientSession(auth=auth) as s:
        while True:
            print("Cursor is", cursor)
            if cursor:
                url = f"https://dt4mob-staging.av.it.pt/api/2/search/things?filter=eq%28namespace%2C%22equivia%22%29&fields=thingId&option=cursor%28{cursor}%29"
            else:
                url = "https://dt4mob-staging.av.it.pt/api/2/search/things?filter=eq%28namespace%2C%22equivia%22%29&fields=thingId&option=size%28200%29"

            async with s.get(url, ssl=False) as resp:
                data = await resp.json()
                ids.extend(d["thingId"] for d in data["items"])
                if "cursor" not in data:
                    break

                cursor = data["cursor"]

        for id in ids:
            url = f"https://dt4mob-staging.av.it.pt/api/2/things/{id}"
            print("Trying to delete id", id)
            r = await s.delete(url, ssl=False)
            try:
                r.raise_for_status()
            except ClientResponseError:
                print("Failed to delete")


if __name__ == "__main__":
    run(main())
