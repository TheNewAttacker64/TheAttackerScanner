#!/usr/bin/env python3

import argparse
import requests
import fake_useragent
import threading
from queue import Queue
import time
import os
import platform
import easygui
def banner():
  return  """
  
  _______ _                  _   _             _             _____                                 
 |__   __| |            /\  | | | |           | |           / ____|                                
    | |  | |__   ___   /  \ | |_| |_ __ _  ___| | _____ _ _| (___   ___ __ _ _ __  _ __   ___ _ __ 
    | |  | '_ \ / _ \ / /\ \| __| __/ _` |/ __| |/ / _ \ '__\___ \ / __/ _` | '_ \| '_ \ / _ \ '__|
    | |  | | | |  __// ____ \ |_| || (_| | (__|   <  __/ |  ____) | (_| (_| | | | | | | |  __/ |   
    |_|  |_| |_|\___/_/    \_\__|\__\__,_|\___|_|\_\___|_| |_____/ \___\__,_|_| |_|_| |_|\___|_|   
    https://github.com/TheNewAttacker64/TheAttackerScanner                                                                                             

  """
def convert_cert(burpcert, to_pem=True):
    if to_pem:
        if platform.system() == 'Windows':
            os.system("certutil -encode "+burpcert+" burp.pem")
        elif platform.system() == 'Linux':
            os.system("openssl x509 -inform der "+burpcert+" -out burp.pem")
    else:
        print("Conversion to PEM format not requested.")
def generate_user_agent():
    user_agent = fake_useragent.UserAgent().random
    return user_agent


def test_url(url, payload, use_cookies, proxies, result_queue, generate_user_agent, cert_path):
    # Add payload to URL
    url_with_payload = f"{url}{payload}"

    # Send the request with the payload
    headers = {}
    if generate_user_agent:
        headers['User-Agent'] = generate_user_agent()
    if use_cookies:
        cookies = {'cookie1': 'value1', 'cookie2': 'value2'}
        response = requests.get(url_with_payload, headers=headers, cookies=cookies, proxies=proxies, verify=cert_path)
    else:
        response = requests.get(url_with_payload, headers=headers, proxies=proxies, verify=cert_path)

    # Check for SQL injection vulnerabilities in the response text
    sql_keywords = ['error', 'syntax error', 'mysql', 'postgre', 'oracle', 'microsoft', 'informix', 'db2', 'sqlite', 'sybase']
    for keyword in sql_keywords:
        if keyword in response.text.lower():
            result_queue.put((url_with_payload, payload))
            break
    else:
        print(f"[-] No SQL injection vulnerability found at {url_with_payload} Try different payloads")


def test_urls(urls, payload, use_cookies, num_threads, proxies, generate_user_agent, cert_path):
    result_queue = Queue()
    start_time = time.time()

    for url in urls:
        t = threading.Thread(target=test_url, args=(url, payload, use_cookies, proxies, result_queue, generate_user_agent, cert_path))
        t.start()

    for t in threading.enumerate():
        if t != threading.current_thread():
            t.join()

    while not result_queue.empty():
        url, payload = result_queue.get()
        print(f"[+] SQL injection vulnerability found at {url} (payload={payload})")

    elapsed_time = time.time() - start_time
    print(f"Scan completed in {elapsed_time:.2f} seconds.")


if __name__ == '__main__':
    print(banner())
    parser = argparse.ArgumentParser(description='Test a list of URLs for SQL injection vulnerabilities')
    parser.add_argument("--convert-burpcert",action='store_true',help="Convert Burp Cert to a Format suppoerted for this script")
    parser.add_argument('--url', help='Single URL to test for SQL injection vulnerabilities')
    parser.add_argument('url_file', nargs='?', default=None, help='Path to a file containing a list of URLs')
    parser.add_argument('--payload', help='Payload to be used for testing SQL injection vulnerabilities')
    parser.add_argument('--use-cookies', action='store_true', help='Use cookies in requests')
    parser.add_argument('--num-threads', type=int, default=10, help='Number of threads to use (default: 10)')
    parser.add_argument('--proxy', help='Proxy to use for requests (format: http://proxyserver:port)')
    parser.add_argument('--random-user-agent', action='store_true', help='Generate a random user agent for each request')
    parser.add_argument('--cert-path', help='Path to a certificate file for the proxy')
    args = parser.parse_args()
    if args.convert_burpcert:
        cert_file = easygui.fileopenbox(msg='Select Burp Suite certificate file', title='Select certificate file',
                                        filetypes='*.der')
        if cert_file:
            convert_cert(cert_file, to_pem=True)
            print('Certificate converted to PEM format')
            exit()
        else:
            print('No certificate file selected')
            exit()

    if args.url is not None:
        urls = [args.url]
    elif args.url_file is not None:
        with open(args.url_file) as f:
            urls = f.read().splitlines()
    else:
        parser.error('You must specify either a URL or a URL file.')
    if args.payload is None:
        payload = "'"
    else:
        payload = args.payload

    use_cookies = args.use_cookies
    num_threads = args.num_threads

    if args.proxy is not None:
        proxies = {'http': args.proxy, 'https': args.proxy}
    else:
        proxies = None

    if args.random_user_agent:
        generate_user_agent = lambda: fake_useragent.UserAgent().random
    else:
        generate_user_agent = None

    cert_path = args.cert_path

    test_urls(urls, payload, use_cookies, num_threads, proxies, generate_user_agent, cert_path)

