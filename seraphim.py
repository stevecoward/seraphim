import os
import sys
import re
import multiprocessing
import glob
import subprocess
import click

def get_screenshot(js_path):
    subprocess.check_output('phantomjs %s' % js_path, shell=True)

def parse_open_ports(line):
    host_pattern = re.compile(r'Host:\s+?(\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3})')
    host_info_pattern = re.compile(r'^(\d+)/(\w+)/(tcp|udp)//([a-zA-Z|]+)')
    open_ports = []
    if '/open/' not in line:
        return open_ports
    
    host_text, host_info = line.split('Ports: ')
    host_match = host_pattern.findall(host_text)

    if not (host_match or host_info_match):
        return open_ports

    ip = host_match[0]
    for entry in host_info.split(', '):
        host_info_match = host_info_pattern.findall(entry)
        for match in host_info_match:
            port, status, protocol, service = match
            if 'http' in service:
                open_ports.append({
                    'ip': ip,
                    'port': port,
                    'status': status,
                    'protocol': protocol,
                    'service': service,
                })
    return open_ports

@click.command()
@click.option('--file', '-f', help='path to greppable nmap output', required=True)
def main(file):
    for folder in ['output', 'tmp']:
        if not os.path.exists(folder):
            os.mkdir(folder)

    contents = []
    try:
        with open(file, 'r') as fh:
            contents = fh.read()
            contents = contents.split('\n')
    except Exception as e:
        click.secho('[!] FAIL: %s' % e, fg='red')
        sys.exit(1)

    pool = multiprocessing.Pool(multiprocessing.cpu_count() * 2)
    open_ports = filter(None, pool.map(parse_open_ports, contents))

    urls = []
    # fyi the listception black magic below 'flattens' open_ports,
    # which is a list of lists
    for host in [item for sublist in open_ports for item in sublist]:
        is_ssl = True if 'ssl' in host['service'] else False
        url = '%s://%s%s' % ('https' if is_ssl else 'http', host['ip'], ':%s' % host['port'] if host['port'] not in ['80','443'] else '')
        urls.append(('%s_%s' % (host['ip'], host['port']), url))

    for item in urls:
        output_filename, url = item
        contents = ''
        with open('screengrab.js', 'r') as fh:
            contents = fh.read()

        contents = contents.replace('{{ url }}', url).replace('{{ output_filename }}', '%s.png' % output_filename)
        with open('tmp/%s.js' % output_filename, 'w') as fh:
            fh.write(contents)

    js_files = glob.glob('tmp/*.js')
    multi_get = filter(None, pool.map(get_screenshot, js_files))
    pool.close()

    map(os.remove, js_files)

if __name__ == '__main__':
    main()
