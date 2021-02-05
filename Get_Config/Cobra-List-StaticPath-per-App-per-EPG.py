#!/usr/bin/env python


import requests.packages.urllib3

requests.packages.urllib3.disable_warnings()

from cobra.mit.access import *
from cobra.mit.session import *


apicUrl = 'https://X.X.X.X'
loginSession = LoginSession(apicUrl, 'admin', 'password')
moDir = MoDirectory(loginSession)
moDir.login()

appList = moDir.lookupByClass("fvAp", parentDn= 'uni/tn-PBLAVIER')
#print(appList[0].rn)
for app in appList:
    print '\n'
    print 'Application Profile: ', app.name
    dn = app.dn
    epgList = moDir.lookupByClass("fvAEPg", parentDn= dn)
    for epg in epgList:
        print '\n'
        print 'EPG: ', epg.name
        dn = epg.dn
        staticPathList = moDir.lookupByClass("fvRsPathAtt", parentDn= dn)
        for staticPath in staticPathList:
            print 'path: ', staticPath.tDn, 'Encap: ', staticPath.encap, 'Mode: ', staticPath.mode



moDir.logout()
