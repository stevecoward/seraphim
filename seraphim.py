#!/usr/bin/env python
import argparse
import asyncio
import os
import re
from playwright.async_api import async_playwright


async def take_screenshot(url):
    filename = re.sub(r'https?:\/\/', '', url)
    filename = filename.replace(':','_')
    
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context(ignore_https_errors=True)
        page = await context.new_page()
        try:
            await page.goto(url, timeout=10000)
            await page.screenshot(path=f'screenshots/{filename}.png')
            await browser.close()
        except Exception as e:
            print(f'{url} error: {e}')


def build_url_list(parsed_data):
    urls = []
    for item in parsed_data:
        address = item['address']
        for result in item['results']:
            scheme = 'http'
            if '443' in result['port'] or result['service'] == 'https':
                scheme = 'https'
            urls.append(f'{scheme}://{address}:{result["port"]}')
    return urls


def extract_data(fh_readlines):
    parsed_data = []
    host_pattern = re.compile(r'Host: (?P<address>\d+\.\d+\.\d+\.\d+).*?Ports: (?P<ports>(?:\d+/(?:open|closed)/(?:tcp|udp)//[^/]+///(?:,\s*)?)*)')
    
    for line in fh_readlines:
        if line.startswith('#'): continue
        
        matches = re.search(host_pattern, line)
        if not matches: continue
        
        match_groups = matches.groupdict()
        match_groups.update({'results': []})
        port_pattern = r'(?P<port>\d+)/(?P<status>open|closed)/(?P<protocol>tcp|udp)//(?P<service>[^/]+)///'
        
        for match in re.finditer(port_pattern, match_groups['ports']):
            match_groups['results'].append(match.groupdict())
        match_groups.pop('ports')
        
        extract_targets = [item for item in match_groups['results'] if item['status'] == 'open' and ('http' in item['service'] or '443' in item['port'])]
        if len(extract_targets):
            match_groups['results'] = extract_targets
            parsed_data.append(match_groups)
    
    return parsed_data


async def main(file_path: str, threads: int):
    parsed_data = []
    tasks = []
    
    if not os.path.exists('screenshots'):
        os.mkdir('screenshots')
    
    with open(file_path, 'r') as fh:
        parsed_data = extract_data(fh.readlines())

    [tasks.append(asyncio.create_task(take_screenshot(url))) for url in build_url_list(parsed_data)]
    
    await asyncio.gather(*tasks)    

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='extract web services from an nmap file and grab screenshots')
    parser.add_argument('-f', '--file', required=True, help='greppable nmap file')
    args = parser.parse_args()
    
    asyncio.run(main(args.file))
