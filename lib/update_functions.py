import urllib2


def check_update():
    proxy = urllib2.ProxyHandler({'http': 'http://krivospickiy_a@mel.local:makesome@192.168.0.242:8080'})

    auth = urllib2.HTTPBasicAuthHandler()
    opener = urllib2.build_opener(proxy, auth, urllib2.HTTPHandler)
    urllib2.install_opener(opener)

    response = urllib2.urlopen('https://pbs.twimg.com/profile_images/578218545416278016/pCKwQ5ik.png')
    html = response.read()
    print html


def version(major=0, minor=0, build=0, revision=0):
    return str(str(major) + '.' + str(minor) + '.' + str(build) + '.' + str(revision))

