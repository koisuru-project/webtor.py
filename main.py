import re
import json
import base64
import asyncio
import hashlib
import datetime
import urllib.parse

import aiohttp
import aiofiles
import bencodepy


async def main(nyaa_id):
    async with aiohttp.ClientSession() as session:
        async with session.get("https://webtor.io/") as webtor_response:
            text = await webtor_response.text()

            with open("text", "w") as f:
                f.write(text)
            loads = json.loads(
                base64.b64decode(
                    re.search(
                        r"FIG__\s+=\s+'(.+)';\s+window\.__INJECT_HASH__\s+=\s+'';\s+window\.__INJECT_CODE__\s+=\s+\"\";\s+<\/script>\s+<div\s+id=\"preloader\"\s+class=\"hide\">",
                        text,
                    )[1]
                )
            )
            # print(loads)
            sdk = loads["sdk"]
            api_url = sdk["apiUrl"]
            api_key = sdk["apiKey"]
            url_search = re.search(
                r"(.+)(a.+)",
                api_url,
            )
            torrent = f"{nyaa_id}.torrent"
            search_token = re.search(
                r"<script\s+type=\"text/javascript\">\s+window\.__TOKEN__\s+=\s+'(.+?)';\s+window\.__CON",
                text,
            )
            token = search_token[1]
            url = f"{api_url}/ext/{urllib.parse.quote(base64.b64encode(f'https://nyaa.si/download/{torrent}'.encode()))}/{torrent}?token={token}&api-key={api_key}"
        async with session.get(url) as ext_response:
            bdecode = bencodepy.bdecode(await ext_response.read())
            info = bdecode[b"info"]
            infohash = hashlib.sha1(bencodepy.bencode(info)).hexdigest()
        async with session.get(
            f"{api_url}/subdomains.json?infohash={infohash}&use-bandwidth=false&use-cpu=true&skip-active-job-search=false&pool=seeder&token={token}&api-key={api_key}"
        ) as response:
            data = (await response.json())[1]
            name = info[b"name"]
            search = re.search(
                r"u=24145874\",\"authURL\":\"\\u002Fauth\\u002Fpatreon\",\"userID\":\"(.+)\",\"downloadI",
                text,
            )[1]
            filename = f'{name.decode()}.zip'
        async with session.get(
            f"{url_search[1]}{data}.{url_search[2]}/{infohash}/{urllib.parse.quote(name,'()')}~arch/{filename}?user-id={search}&download-id={hashlib.md5(f'{search}{infohash}{datetime.datetime.now()}'.encode()).hexdigest()}&token={token}&api-key={api_key}"
        ) as response:
            if response.status == 500:
                raise Exception('Torrent belum tersedia di server. Coming soon (Fitur push ke server).')
            print(response)
            async with aiofiles.open(filename, 'wb') as f:
                async for chunks in response.content.iter_any():
                    await f.write(chunks)
            # data = await response.text()


nyaa_id = 1659202
loop = asyncio.get_event_loop()
loop.run_until_complete(main(nyaa_id))
