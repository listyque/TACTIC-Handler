import urlparse
url = 'skey://Mushroom/exam/props?project=exam&code=PROPS00004'
r1 = urlparse.urlsplit(url)

print(r1)
print(r1.scheme)
