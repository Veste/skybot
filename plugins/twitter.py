"""
twitter.py: written by Scaevolus 2009
retrieves most recent tweets
"""

import re
import random
import urllib2
from lxml import etree
from time import strptime, strftime

from util import hook


def unescape_xml(string):
    # unescape the 5 chars that might be escaped in xml

    # gratuitously functional
    # return reduce(lambda x, y: x.replace(*y), (string,
    #     zip('&gt; &lt; &apos; &quote; &amp'.split(), '> < \' " &'.split()))

    # boring, normal
    return string.replace('&gt;', '>').replace('&lt;', '<').replace('&apos;',
                    "'").replace('&quote;', '"').replace('&amp;', '&')


@hook.command
def twitter(inp):
    ".twitter <user>/<user> <n>/<id>/#<hashtag> -- gets last/<n>th tweet from"\
    "<user>/gets tweet <id>/gets random tweet with #<hashtag>"
    inp = inp.strip()
    if not inp:
        return twitter.__doc__


    url = 'http://twitter.com'
    getting_nth = False
    getting_id = False
    searching_hashtag = False
    
    time = 'status/created_at'
    text = 'status/text'
    if re.match(r'^\d+$', inp):
        getting_id = True
        url += '/statuses/show/%s.xml' % inp
        screen_name = 'user/screen_name'
        time = 'created_at'
        text = 'text'
    elif re.match(r'^\w{1,15}$', inp):
        url += '/users/show/%s.xml' % inp
        screen_name = 'screen_name'
    elif re.match(r'^\w{1,15}\s+\d+$', inp):
        getting_nth = True
        name, num = inp.split()
        if int(num) > 3200:
            return 'error: only supports up to the 3200th tweet'
        url += '/statuses/user_timeline/%s.xml?count=1&page=%s' % (name, num)
        screen_name = 'status/user/screen_name'
    elif re.match(r'^#\w+$', inp):
        url = 'http://search.twitter.com/search.atom?q=%23' + inp[1:]
        searching_hashtag = True
    else:
        return 'error: invalid request'

    try:
        xml = urllib2.urlopen(url).read()
    except urllib2.HTTPError, e:
        errors = {400 : 'bad request (ratelimited?)',
                401: 'tweet is private',
                404: 'invalid user/id',
                500: 'twitter is broken',
                502: 'twitter is down ("getting upgraded")',
                503: 'twitter is overloaded (lol, RoR)'}
        if e.code == 404:
            return 'error: invalid ' + ['username', 'tweet id'][getting_id]
        if e.code in errors:
            return 'error: ' + errors[e.code]
        return 'error: unknown'
    except urllib2.URLerror, e:
        return 'error: timeout'

    tweet = etree.fromstring(xml)

    if searching_hashtag:
        ns = '{http://www.w3.org/2005/Atom}'
        tweets = tweet.findall(ns + 'entry/' + ns + 'id')
        if not tweets:
            return 'error: hashtag not found'
        id = random.choice(tweets).text
        id = id[id.rfind(':') + 1:]
        print id
        return twitter(id)

    if getting_nth:
        if tweet.find('status') is None:
            return 'error: user does not have that many tweets'

    time = tweet.find(time)
    if time is None:
        return 'error: user has no tweets'

    time = strftime('%Y-%m-%d %H:%M:%S', 
             strptime(time.text,
               '%a %b %d %H:%M:%S +0000 %Y'))
    text = unescape_xml(tweet.find(text).text.replace('\n', ''))
    screen_name = tweet.find(screen_name).text

    return "%s %s: %s" % (time, screen_name, text)
