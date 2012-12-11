""" 
Module hosting the class representing connection to the
gog.com web API.
"""
import oauth2 as oauth
import urlparse
import requests
import sys
import urllib
import json
import os


class GogConnection:
    """ Class representing the connection to gog.com """

    auth_token = None

    def __init__(self):

        self.url_base = "https://api.gog.com/en/"
        self.protocol = "downloader2/status/RELEASE/"
        data = self.__obtain_url_details()
        self.temp_token = data["oauth_get_temp_token"]
        self.auth_temp_token = data["oauth_authorize_temp_token"]
        self.get_token = data["oauth_get_token"]
        self.user_url = data["get_user_details"]
        self.user_games = data["get_user_games"] # This does not work yet :(
        self.game_details = data["get_game_details"]
        self.game_installer = data["get_installer_link"]
        self.game_extras = data["get_extra_link"]

        client_key = '1f444d14ea8ec776585524a33f6ecc1c413ed4a5'
        client_secret = '20d175147f9db9a10fc0584aa128090217b9cf88'
        self.consumer = oauth.Consumer(client_key, client_secret)

    def __obtain_url_details(self):
        """
        Return a dictionary with the required methods for interacting with
        gog.com and their respective URLs.
        """
        res = requests.get(self.url_base+self.protocol)
        if res.status_code != 200:
            raise Exception("Could not connect to the gog.com API.")
        return json.loads(res.text)["config"] # I should just use res.json maybe



    #returns true only if resp status is 200 else it raises an exception
    def __check_status(self, resp, failure=None):
        """ 
        Method to check the response status.
        Throw an exception when return code isn't 200 else return True.

        Keyword arguments:
        failure -- Custom exception message (default None)

        """
        if resp['status'] == '200':
            return True
        if failure is not None:
            raise Exception(failure)
        raise Exception("Invalid request, response %s." % resp['status'])

    def connect(self, username, password):
        """ Connect to gog.com using the defined username and password. """
        client = oauth.Client(self.consumer)
        #resp, content = client.request(self.url_base+self.temp_token, "GET")
        resp, content = client.request(self.temp_token, "GET")
        self.__check_status(resp)
        request_token = dict(urlparse.parse_qsl(content))
        temp_secret = request_token['oauth_token_secret']
        temp_token = request_token['oauth_token']
        token = oauth.Token(temp_token, temp_secret)
        auth_client = oauth.Client(self.consumer, token)
        print "Authenticating..."
        enc_url = urllib.urlencode({ 'password' : password, 
                                     'username' : username })
        login_url = "%s/?%s" % (self.auth_temp_token, enc_url)
        resp, content = auth_client.request(login_url, "GET")
        error_message = "%s\n%s" % ("Unable to authenticate.\n", 
                                    "Check your connection, " 
                                    "your username and your password")
        self.__check_status(resp, error_message)
        oauth_verifier = dict(urlparse.parse_qsl(content))['oauth_verifier']
        token.set_verifier(oauth_verifier)
        client = oauth.Client(self.consumer, token)
        enc_url = urllib.urlencode({ 'oauth_verifier' : oauth_verifier })
        token_url = "%s/?%s" % (self.get_token, enc_url)
        resp, content = client.request(token_url)
        self.__check_status(resp, "Couldn't authenticate connection.\n"
                                  "Please verify your internet connection "
                                  "is working properly.")
        final_token = dict(urlparse.parse_qsl(content))['oauth_token']
        final_secret = dict(urlparse.parse_qsl(content))['oauth_token_secret']
        self.set_auth_token(final_token, final_secret)

        self.auth_token = oauth.Token(final_token, final_secret)
        client = oauth.Client(self.consumer, self.auth_token)
        print "Success"

    def set_auth_token(self, token, secret):
        """ Set the authentication token using a token and a secret key """
        self.auth_token = oauth.Token(token, secret)

    def get_user_data(self):
        """ Get user profile data from gog.com """
        if not ('auth_token' in dir(self)):
            raise Exception("Not logged in correctly.")
        
        client = oauth.Client(self.consumer, self.auth_token)
        resp, content = client.request(self.user_url)
        self.__check_status(resp)
        return content

    def __obtain_installer_name(self, installer):
        """ 
        Return the name of the setup.exe file without the game name and id
        path added before it.
        """
        return installer[installer.find("setup_"):]

    def download_game(self, gameid, location):
        """ 
        Download the game with the specified gameid 
        from gog.com to the specified location. 
        """
        # this should work most of the time but I am not 100% sure 
        client = oauth.Client(self.consumer, self.auth_token)
        resp, content = client.request(self.game_details+gameid)
        self.__check_status(resp)
        installers = json.loads(content)["game"]["win_installer"]
        total_size = 0
        download_urls = {}
        for installer_data in installers:
            installer_id = installer_data["id"]
            # We need to replace , with . for decimal places
            installer_size = installer_data["size_mb"].replace(',','.')
            downloader = "%s/%s/%s/" % (self.game_installer,
                                        gameid, installer_id)
            resp, content = client.request(downloader)
            self.__check_status(resp)
            download_url = json.loads(content)["file"]["link"]
            download_url = download_url[:download_url.find('&fileExtForIe=.exe')]
            local_path = installer_data["path"]
            # Remove the part that is not relevant to the filename
            local_path = self.__obtain_installer_name(local_path)
            download_urls[local_path] = download_url
            total_size += float(installer_size)

        size_in_kb = installer_size*1024
        chunk = 512*1024 # 512KB each chunk
        downloaded = 0
        print "Need to obtain %sMB of data" % total_size
        for key in download_urls.keys():
            path = os.path.join(location, key)
            if os.path.exists(path):
                raise Exception("[%s]: A file already exists at this location, "
                                "cannot proceed with download." % path)
            percentage = 0
            print "0%"
            req = urllib.urlopen(download_urls[key])
            with open(path, 'wb') as file_handle:
                while True:
                    new_percentage = int((float(downloaded)/
                                         (float(size_in_kb)*1024))*100)
                    if new_percentage != percentage:
                        percentage = new_percentage
                        print "%s%%" % percentage
                    data = req.read(chunk)
                    if not data:
                        break
                    downloaded += chunk
                    file_handle.write(data)
                print "[%s]: %d KB written" % (path, (downloaded/1024))
        entry_path = installers[0]["path"]
        entry_path = self.__obtain_installer_name(entry_path)
        return os.path.join(location, entry_path)

