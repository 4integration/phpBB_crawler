import scrapy
import re 
from Forum_Scraper.items import ForumScraperItem
from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.contrib.linkextractors import LinkExtractor
from scrapy.http import Request, FormRequest

class ForumSpider(CrawlSpider):
    name = "spider_name_here"
    allowed_domains = ["your_allowed_domains.com"]
    login_page = 'login_page_here.com'
    start_urls = ['start_crawling_here.com']
    rules = (
       # Rules here are to specify subforum f=345 and to follow threads within that subforum
       Rule(LinkExtractor(allow=(r'f=345&t=[0-9]{2,5}$',)), callback= 'parse_page', follow=True), 
       Rule(LinkExtractor(allow=(r'f=345&t=[0-9]{2,5}&start=[0-9]{2,5}$',)), callback= 'parse_page', follow=True),
       Rule(LinkExtractor(allow=(r'f=345&start=[0-9]{2,5}$',)), callback= 'parse_page', follow=True),
    )

    # Script starts here and begins login attempt
    def start_requests(self):
        yield Request(
            url=self.login_page,
            callback=self.login)

    # Return form with login information
    def login(self, response):
        """Generate a login request."""
        return FormRequest.from_response(response,
                formdata={'username': 'your_username', 'password': 'your_password'},
                callback=self.check_login_response)

    # Check whether login was successful
    # Success message depends on website, but phpbb error is "You have specified an incorrect password"
    def check_login_response(self, response):
        if "You have specified an incorrect password" in response.body:
            self.log("Login failed.")
        else:
            self.log("Successfully logged in. Let's start crawling!")
            # Now the crawling can begin.
            for url in self.start_urls:
                # explicitly ask Scrapy to run the responses through rules
                yield Request(url, callback=self.parse)



    def parse_page(self, response):
	'''
	My use for this bot was to create word counts for each author in a phpBB forum thread.

	In this method I find each author in a given thread ("postauthor"), find each post ("postbody"), 
	and the title of the thread ("titles"). Authors and post content are added to a list. The post content
	is then split and a word count is generated.
	'''
        # Extract author names from post
        author = response.xpath('//div[@class="postauthor"]').re('>([a-zA-Z0-9]*)<')
        # Extra post contents from post
        postContent = response.xpath('//div[@class="postbody"]').re('<div class="postbody">(.*)<.*')
        # Post subject title
        postSubject = postSubject = response.xpath('//a[@class="titles"]').re('>(.*)<')
        
        # Author name list
        authorList = []
        for a in author:
            authorList.append(a)
        
        # Post content list
        pcList = []
        
        # Regexes for various tags
        # Regex to remove <br> tag
        brTag = re.compile("<br>")
        # Regex to remove nested <div> tag
        divTag = re.compile("<div.*</div>")
        # Regex to remove nested <a href> tag
        ahrefTag = re.compile("<a href.*</a>")
        # Regex to remove nested <img src> tag
        imgsrcTag = re.compile("<img src.*>")
        # Regex to remove any additional <> or </> tags
        tags = re.compile("<.*>")
        closeTags = re.compile("<//.*>")
        
        # Iterate over post and substitute using above regexes
        for c in postContent:
            c = brTag.sub("", c)
            c = divTag.sub("", c)
            c = ahrefTag.sub("", c)
            c = imgsrcTag.sub("", c)
            c = tags.sub("", c)
            c = closeTags.sub("", c)
              
            # Split c on ' ' to get word count
            wordCount = c.split()
            # Add length of wordCount to post count list
            pcList.append(len(wordCount))
        
        # Create PostCountItem and add results
        item = ForumScraperItem()
        item['author'] = authorList
        item['wordCount'] = pcList
        item['postSubject'] = postSubject
        return item
