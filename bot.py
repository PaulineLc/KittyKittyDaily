#!/usr/bin/env python
# -*- coding: utf-8 -*-

import tweepy
import json
import os
from PIL import Image
import logging
import sys
from resize_gif import resize_gif
from scrap_reddit import RedditPost
import urllib.request

logging.basicConfig(filename='error.log',
                    filemode='a',
                    level=logging.INFO,
                    format='%(asctime)s\n%(message)s')


class TwitterBot:

    """A Twitter bot that scraps content from Reddit and post it to Twitter."""

    MAX_MESSAGE_LENGTH = 140  # maximum status length allowed by Twitter
    MAX_IMAGE_SIZE_BYTES = 3072000  # maximum size of media allowed by Twitter
    LINK_LENGTH = 23  # Links posted to Twitter are always counted as 23 characters regardless of their actual length

    def __init__(self, twitter_account, config_file):
        self.twitter_account = twitter_account
        self.reddit_post = RedditPost(twitter_account, config_file)
        self.config_file = config_file
        self.picture = twitter_account + "_picture"
        self._CONSUMER_KEY = None
        self._SECRET_CONSUMER_KEY = None
        self._ACCESS_TOKEN = None
        self._SECRET_ACCESS_TOKEN = None
        self._hashtags = None
        self._error_message = None

    @property
    def CONSUMER_KEY(self):
        if not self._CONSUMER_KEY:
            self.read_config_file()
        return self._CONSUMER_KEY

    @property
    def SECRET_CONSUMER_KEY(self):
        if not self._SECRET_CONSUMER_KEY:
            self.read_config_file()
        return self._SECRET_CONSUMER_KEY

    @property
    def ACCESS_TOKEN(self):
        if not self._ACCESS_TOKEN:
            self.read_config_file()
        return self._ACCESS_TOKEN

    @property
    def SECRET_ACCESS_TOKEN(self):
        if not self._SECRET_ACCESS_TOKEN:
            self.read_config_file()
        return self._SECRET_ACCESS_TOKEN

    @property
    def hashtags(self):
        if not self._hashtags:
            self.read_config_file()
        return self._hashtags

    @property
    def error_message(self):
        if not self._error_message:
            self.read_config_file()
        return self._error_message

    def read_config_file(self):
        """
        Reads the config file and set the following attributes:
            _CONSUMER_KEY: the consumer key of the Twitter app
            _SECRET_CONSUMER_KEY: the secret consumer key of the Twitter app
            _ACCESS_TOKEN: the access token of the twitter app
            _SECRET_ACCESS_TOKEN: the secret access token of the Twitter app
            _hashtags: the list of hashtags to be added to the Twitter status
            _error_message: an error message to be twitted in case of error
        """

        with open(self.config_file) as data_file:
            data = json.load(data_file)

        data = data[self.twitter_account]
        self._CONSUMER_KEY = data["consumer_key"]
        self._SECRET_CONSUMER_KEY = data["secret_consumer_key"]
        self._ACCESS_TOKEN = data["access_token"]
        self._SECRET_ACCESS_TOKEN = data["secret_access_token"]
        self._hashtags = data["hashtags"]
        self._error_message = data["error_message"]

    def download_picture(self):
        """
        Downloads the picture from the top reddit post and resizes it if its size is above the maximum size allowed.
        """
        self.picture = self.picture + self.reddit_post.picture_extension
        urllib.request.urlretrieve(self.reddit_post.picture_url, self.picture)
        picture_size = os.stat(self.picture).st_size
        if picture_size > type(self).MAX_IMAGE_SIZE_BYTES:
            logging.exception("********File too large********")
            logging.error("Content: " + self.reddit_post.url)
        # else:
        #     try:
        #         im = Image.open(self.picture)
        #         im_format = im.format
        #     except OSError as err:
        #         print(type(err), err)
        #         logging.exception('********Unknown file extension********')
        #         logging.error("file:" + self.reddit_post.url)
        #         # if the file is too large and its format is unknown, PIL can't resize it so we won't be able to post it
        #         sys.exit()
        #     new_name = self.picture + "." + im_format
        #     os.rename(self.picture, new_name)
        #     self.picture = new_name
        #     while picture_size > type(self).MAX_IMAGE_SIZE_BYTES:
        #         if im_format == "GIF":
        #             resize_gif(self.picture)
        #             picture_size = os.stat(self.picture).st_size
        #         else:
        #             self.resize_picture()
        #             picture_size = os.stat(self.picture).st_size

    # def resize_picture(self):
    #     """Resize the picture if it is above the maximum size allowed"""
    #     picture = Image.open(self.picture).convert('RGB')
    #     picture = picture.resize((picture.size[0] // 2, picture.size[1] // 2), Image.ANTIALIAS)
    #     picture.save(self.picture, optimize=True, quality=85)

    def define_status_update(self):
        """
        Prepare the status update. It takes the title of the top reddit post, the url to the post, and the list of
        hashtags. It will add hashtags until it runs out of characters (140 characters max).
        """
        message = self.reddit_post.title
        via = " via "
        if len(message) + len(via) + type(self).LINK_LENGTH > 140:
            eom_characters = "..."
            message = message[:140 - len(eom_characters) - len(via) - type(self).LINK_LENGTH] + eom_characters
        else:
            i = 0
            while i < len(self.hashtags) and len(message) + len(via) + type(self).LINK_LENGTH + len(self.hashtags[i]) < type(self).MAX_MESSAGE_LENGTH:
                message += " " + self.hashtags[i]
                i += 1
        final_message = message + via + self.reddit_post.url
        return final_message

    def post_to_twitter(self):
        """
        Posts a picture and a status to Twitter.
        Will log errors to error.log.
        """
        self.download_picture()
        status_update = self.define_status_update()
        auth = tweepy.OAuthHandler(self.CONSUMER_KEY, self.SECRET_CONSUMER_KEY)
        auth.set_access_token(self.ACCESS_TOKEN, self.SECRET_ACCESS_TOKEN)
        api = tweepy.API(auth)
        try:
            media = api.upload_chunked(self.picture)
            api.update_status(status="Testing a new GIF / Video integration :-)!", media_ids=[media.media_id])
            # api.update_with_media(self.picture, status=status_update)
        except tweepy.error.TweepError as err:
            print(type(err), err)
            logging.exception('********Tweepy error********')
            logging.error("status update: " + status_update)
        except Exception as err:
            print(type(err), err)
            logging.exception('******Unexpected error******')
            logging.error("status update: " + status_update)
        finally:
            os.remove(self.picture)


if __name__ == "__main__":
    botty_mcbotface = TwitterBot("AllThingsKute", "config.json")
    botty_mcbotface.post_to_twitter()
