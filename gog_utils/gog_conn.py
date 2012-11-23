#!/usr/bin/env python

import oauth2 as oauth
import urlparse
import getpass
import sys
import urllib
import time
import json
import os


class GogConnection:


    #TODO: add support for dynamic protocol URL
    def __init__(self):
        self.url_base = "https://api.gog.com/en/"
        self.protocol = "downloader2/status/RELEASE/"
        self.temp_token = "oauth/initialize"
        self.auth_temp_token = "oauth/login"
        self.get_token = "oauth/token"
        
        client_key = '1f444d14ea8ec776585524a33f6ecc1c413ed4a5'
        client_secret = '20d175147f9db9a10fc0584aa128090217b9cf88'
        self.consumer = oauth.Consumer(client_key, client_secret)

    #returns true only if resp status is 200 else it raises an exception
    def __check_status(self, resp):
        if resp['status'] == '200':
            return True
        raise Exception("Invalid request, response %s." % resp['status'])

    def connect(self, username, password):
        client = oauth.Client(self.consumer)
        resp, content = client.request(self.url_base+self.temp_token, "GET")
        self.__check_status(resp)
        request_token = dict(urlparse.parse_qsl(content))
        temp_secret = request_token['oauth_token_secret']
        temp_token = request_token['oauth_token']
        token = oauth.Token(temp_token, temp_secret)
        auth_client = oauth.Client(self.consumer,token)
        print "Authenticating..."
        login_url = "%s%s/?%s" % (self.url_base, self.auth_temp_token, urllib.urlencode({ 'password' : password, 'username' : username }))
        resp, content = auth_client.request(login_url, "GET")
        self.__check_status(resp)
        oauth_verifier = dict(urlparse.parse_qsl(content))['oauth_verifier']
        token.set_verifier(oauth_verifier)
        client = oauth.Client(self.consumer,token)
        token_url = "%s%s/?%s" % (self.url_base, self.get_token, urllib.urlencode({ 'oauth_verifier' : oauth_verifier }))
        resp, content = client.request(token_url)
        self.__check_status(resp)
        final_token = dict(urlparse.parse_qsl(content))['oauth_token']
        final_secret = dict(urlparse.parse_qsl(content))['oauth_token_secret']
        self.set_auth_token(final_token, final_secret)

        self.auth_token = oauth.Token(final_token, final_secret)
        client = oauth.Client(self.consumer,self.auth_token)
        print "Success"

    def set_auth_token(self, token, secret):
        self.auth_token = oauth.Token(token, secret)

    def get_user_data(self):
        if not ('auth_token' in dir(self)):
            raise Exception("Not logged in correctly.")
        
        client = oauth.Client(self.consumer,self.auth_token)
        resp, content = client.request("https://api.gog.com/en/downloader2/user/")
        self.__check_status(resp)
        return content

    def download_game(self, gameid, location):
        # this should work most of the time but I am not 100% sure 
        downloader = "%sdownloader2/installer/%s/0/" % (self.url_base, gameid)
        client = oauth.Client(self.consumer,self.auth_token)
        resp, content = client.request(downloader)
        self.__check_status(resp)
        download_url = json.loads(content)["file"]["link"]
        download_url = download_url[:download_url.find('&fileExtForIe=.exe')]
        req = urllib.urlopen(download_url)
        chunk = 512*1024 # 512KB each chunk
        size = 0
        print location
        path = os.path.join(location,"setup_%s.exe" % gameid)
        print path
        with open(path,'wb') as fp:
            while True:
                sys.stdout.write('.')
                sys.stdout.flush()
                data = req.read(chunk)
                if not data:
                    break
                size += chunk
                fp.write(data)
            print "%d KB written" % (size/1024)
        return path



