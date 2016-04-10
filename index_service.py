# -*- coding: utf-8 -*-
from __future__ import print_function
from HTMLParser import HTMLParser
from twisted.web import server, resource
from twisted.web.client import Agent, FileBodyProducer
from twisted.internet.defer import Deferred
from twisted.internet import reactor, protocol
from database_api import DatabaseAPI
from StringIO import StringIO
import urllib2
import json



""" Index microservice class """
class IndexService(resource.Resource):
    isLeaf = True

    def __init__(self, host, port, dbname, user, password, stopword_file_path):
        self.index = DatabaseAPI(host, port, dbname, user, password)
        self.indexer = Indexer(stopword_file_path)
        self.startup_routine()
        reactor.listenTCP(8001, server.Site(self))
        reactor.run()

    # Asks the user for some questions at startup.
    def startup_routine(self):
        while True:
            print("Options:")
            print("1. Initialize database")
            print("2. Index all articles from content")
            print("3. Start service")
            print(">> ", end="")
            user_input = str(raw_input())
            if user_input == '1':
                self.initialize_database()   
            elif user_input == '2':
                self.index_content()
            elif user_input == '3':
                print("Starting index service. Use Ctrl + c to quit.")
                break
            else:
                print("Option has to be a number between 1 and 3")
                continue

    # Creates new clean tables in the database
    def initialize_database(self):
        yes = set(['Y', 'y', 'Yes', 'yes', 'YES'])
        no = set(['N', 'n', 'No', 'no', 'NO'])
        while True:
            print("This will delete any existing data and reset the database.")
            print("Are you sure you want to continue? [Y]es/[N]o")
            print(">> ", end="")
            user_input = str(raw_input())
            if user_input in yes:
                self.index.make_tables()
                break
            elif user_input in no:
                break
            else:
                continue

    # Indexes all articles from the content microservice.
    def index_content(self):
        # **** TODO: dont index already indexed articles ****
        host = 'http://127.0.0.1:8002'  # content host - **** TODO: fetched from dht node network ****
        urls = self.get_all_articles(host)
        print(urls)
        #for url in urls:
        #    self.index_page(url)

    # Asks content service for urls to all articles. Returns list of the urls.
    def get_all_articles(self, host):
        request = json.dumps({"Request" : "get all articles"})  
        agent = Agent(reactor) 
        d = agent.request("POST", host, None, FileBodyProducer(StringIO(request)))
        d.addCallback(self.cbRequest)
        #d.addBoth(self.cbShutdown)
        #reactor.run()
        
    def cbRequest(self, response):
        finished = Deferred()
        response.deliverBody(BeginningPrinter(finished))
        return finished   

    # Indexes page at url.
    def index_page(self, url):
        page = self.make_index(url)
        self.index.insert(page)

    # Handles POST requests
    def render_POST(self, request):
        d = json.load(request.content)
        if d['Partial'] == "True":
            return "not implemented yet"
        if d['Partial'] == "False":
            word = d['Query']
            print('ayy')
            data = index.query("SELECT * FROM wordfreq WHERE word=(%s)", (word))
            print(data)
        else:
            print("you got mail")
            return('result')



""" Request Client """
class RequestClient(protocol.Protocol):
    def __init__(self, finished):
        self.finished = finished
        self.remaining = 1024 * 10
        self.data = ""

    def dataReceived(self, bytes):
        if self.remaining:
            display = bytes[:self.remaining]
            self.data += display
            self.remaining -= len(display)

    def connectionMade(self):
        self.transport.write(self.factory.requestquery)
        self.transport.loseConnection()

    def connectionLost(self, reason):
        print('Finished receiving body:', reason.getErrorMessage())
        self.finished.callback(None)
    


""" Basic indexer of HTML pages """
class Indexer:

    stopwords = None

    def __init__(self, stopword_file_path):
        self.stopwords = set([''])

        # Reading in the stopword file:
        with open(stopword_file_path, 'r') as f:
            for word in f.readlines():
                self.stopwords.add(word.strip())

    # Takes an url as arguments and indexes the article at that url. Returns a list of tuple values.
    def make_index(self, url):
        # Retriving the HTML source from the url:
        req = urllib2.Request(url)
        response = urllib2.urlopen(req)
        page = str(response.read()) #.decode('utf-8'))
        response.close()

        # Parseing the HTML:
        parser = Parser()
        parser.feed(page)
        content = parser.get_content()
        parser.close()

        # Removing stopwords:
        unique_words = set(content).difference(self.stopwords)

        # Making a list of tuples: (url, word, wordfreq):
        values = []
        for word in unique_words:
            values.append((url, word, content.count(word)))

        return values



""" Basic parser for parsing of html data """
class Parser(HTMLParser):
	
    content = []
    tags_to_ignore = set(["script"]) # Add HTML tags to the set to ignore the data from that tag.
    ignore_tag = False

    # Keeps track of which tags to ignore data from.
    def handle_starttag(self, tag, attrs):
        if tag in self.tags_to_ignore:
            self.ignore_tag = True
        else:
            self.ignore_tag = False
      
    # Handles data from tags.  
    def handle_data(self, data):
        if data.strip() == "" or self.ignore_tag:
            return

        for word in data.split():
            if word.strip() == "":
                continue
            self.content.append(word.lower().strip("'.,;:/&()=?!`´´}][{-_"))

    # Get method for content.
    def get_content(self):
        return self.content


