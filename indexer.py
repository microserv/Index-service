# -*- coding: utf-8 -*-
import urllib.request
from html.parser import HTMLParser


""" Basic indexer of HTML pages """
class Indexer:

    stopwords = set([''])

    def __init__(self, stopword_file):
        # Reading in the stopword file
        with open(stopword_file, 'r', encoding='utf-8') as f:
            for word in f.readlines():
                self.stopwords.add(word.strip())

    def make_index(self, url):
        # Retriving the HTML source from the url
        with urllib.request.urlopen(url) as html:
            page = str(html.read().decode('utf-8'))

        # Parse the HTML
        parser = Parser()
        parser.feed(page)
        content = parser.get_content()
        parser.close()

        # Removing stopwords
        unique_words = set(content).difference(self.stopwords)

        # Making a list of tuples: (url, word, wordfreq)
        values = []
        for word in unique_words:
            values.append((url, word, content.count(word)))

        return values


"""Basic parser for parsing of html data"""
class Parser(HTMLParser):
	
    content = []
    tags_to_ignore = set(["script"]) # Add HTML tags to the set to ignore the data from that tag
    ignore_tag = False

    def handle_starttag(self, tag, attrs):
        if tag in self.tags_to_ignore:
            self.ignore_tag = True
        else:
            self.ignore_tag = False
        
    def handle_data(self, data):
        if data.strip() == "" or self.ignore_tag:
            return

        for word in data.split():
            if word.strip() == "":
                continue
            self.content.append(word.lower().strip("'.,;:/&()=?!`´´}][{-_"))

    def get_content(self):
        return self.content


