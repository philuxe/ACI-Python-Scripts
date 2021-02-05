#!/usr/bin/env python

# #################################################################################################### The script
# - takes the CSV file and create Static Paths in EPG's
# CSV parameters are : Tenant, Pod, Encap (vlan id), Node (is leaf
# id), Port (port number only), Application Name, EPG Name, Mode (regular is trunk, untagged is access)
# This script can only create static paths for regular ports (no port-channel support)
# ####################################################################################################

# Disable SSL WARNING for APIC self signed Certs
import requests.packages.urllib3
requests.packages.urllib3.disable_warnings()

# list of packages to be imported
import csv
import cobra.mit.access
import cobra.mit.naming
import cobra.mit.request
import cobra.mit.session
import cobra.model.fv
from cobra.internal.codec.xmlcodec import toXMLStr

# log into APIC and create a directory object
ls = cobra.mit.session.LoginSession('https://10.51.123.190', 'admin', 'cisco2020')
md = cobra.mit.access.MoDirectory(ls)
md.login()

# parse the CSV file and loop over each line
with open('ADD-Static-Path-to-EPG-4-RegularPorts-fromCSV.csv') as csvfile:
    reader = csv.DictReader(csvfile, delimiter=';')
    for row in reader:
        print 'Adding the following Static Path to APIC'
        print 'TENANT: ' + str(row['TENANT'])
        print 'POD: ' + str(row['POD'])
        print 'LEAF: ' + str(row['NODE'])
        print 'PORT: ' + str(row['PORT'])
        print 'VLAN_ID: ' + str(row['VLAN'])
        print 'APP_NAME: ' + str(row['APP'])
        print 'EPG_NAME: ' + str(row['EPG'])
        print 'MODE: ' + str(row['MODE'])
        print '\r'

        # create variable and assign CSV values
        csv_tenant = row['TENANT']
        csv_app = row['APP']
        csv_epg = row['EPG']
        csv_pod = row['POD']
        csv_node = row['NODE']
        csv_port = row['PORT']
        csv_vlan = row['VLAN']
        csv_mode = row['MODE']

        # path1 is a string that defines the object DN we want to create
        path1 = 'uni/tn-' + str(csv_tenant) + '/ap-' + str(csv_app) + '/epg-' + str(
            csv_epg) + '/rspathAtt-[' + 'topology/pod-' + str(csv_pod) + '/paths-' + str(
            csv_node) + '/pathep-[eth1/' + str(csv_port) + ']]'

        # path2 is a string that defines the object tDN
        path2 = 'topology/pod-' + str(csv_pod) + '/paths-' + str(csv_node) + '/pathep-[eth1/' + str(csv_port) + ']'

        vlan = 'vlan-' + csv_vlan

        print ("path1", path1)
        print ("path2", path2)

        # the top level object on which operations will be made (this is path1 string in our case)
        # this specifies where the object is going to be created in the MIT
        topDn = cobra.mit.naming.Dn.fromString(str(path1))
        topParentDn = topDn.getParent()
        topMo = md.lookupByDn(topParentDn)

        # build the fvRsPathAtt object
        fvRsPathAtt = cobra.model.fv.RsPathAtt(topMo, tDn=unicode(path2), descr=u'',
                                               primaryEncap=u'unknown', instrImedcy=u'immediate',
                                               mode=unicode(csv_mode),
                                               encap=unicode(vlan))

        # print what we are going to push to APIC
        print toXMLStr(topMo)

        # commit the generated code to APIC
        c = cobra.mit.request.ConfigRequest()
        c.addMo(topMo)
        md.commit(c)

        print '\r'
        print '####################################################################################################################'
        print '\r'
