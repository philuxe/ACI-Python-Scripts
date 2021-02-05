import csv

import requests.packages.urllib3
from cobra.mit.access import MoDirectory, ClassQuery
from cobra.mit.request import ConfigRequest
from cobra.mit.session import LoginSession
from cobra.model.fv import Tenant, Ap, AEPg, RsPathAtt

requests.packages.urllib3.disable_warnings()

# Current Features :
# Support creating static paths for regular ports, port-channel and virtual port-channel
# csv columns must be as follow :
# TENANT;VLAN;NODE;TARGET;APP;EPG;MODE
# regular port target : leaf id and port id (ethx/y) must be supplied
# port-channel : leaf id is numerical, target is the policy-group name
# vpc : leaf id is not evaluated , target is the policy-group name


def apic_logon(url, username, password):
    my_session = LoginSession(url, username, password)
    modir_local = MoDirectory(my_session)
    modir_local.login()
    return modir_local


# format port id = eth1/1
def get_mo_for_interface(nodeid, portid):
    cq = ClassQuery('fabricPathEpCont')
    cq.propFilter = 'eq(fabricPathEpCont.nodeId, "{0}")'.format(nodeid)
    cq.subtree = 'children'
    cq.subtreeClassFilter = 'fabricPathEp'
    req = moDir.query(cq)
    for key in req[0].children:
        if key.name == portid:
            return format(key.dn)  # return a string containing the MO for the requested interface


def get_mo_for_pg(name):
    cq = ClassQuery('fabricProtPathEpCont')
    cq.subtree = 'children'
    cq.subtreeClassFilter = 'fabricPathEp'
    cq.subtreePropFilter = 'eq(fabricPathEp.name, "{0}")'.format(name)
    req = moDir.query(cq)
    for key in req[0].children:
        return format(key.dn)


def create_static_path(tenant_name, app_name, epg_name, path_name, encap_id, mode_name):
    vlan_id = 'vlan-' + encap_id
    uni_mo = moDir.lookupByDn('uni')
    tenant_mo = Tenant(uni_mo, tenant_name)
    app_mo = Ap(tenant_mo, app_name)
    epg_mo = AEPg(app_mo, epg_name)
    rspathatt_mo = RsPathAtt(epg_mo, tDn=path_name, instrImedcy=u'immediate', encap=vlan_id, mode=mode_name)
    config = ConfigRequest()
    config.addMo(tenant_mo)
    moDir.commit(config)


moDir = apic_logon('https://sandboxapicdc.cisco.com', 'admin', 'password')
with open('Test.csv') as csvfile:
    reader = csv.DictReader(csvfile, delimiter=';')
    for row in reader:
        # Checking whether it is regular port or PC/VPC
        node = unicode(str(row['NODE']))
        # make sure node iD is numeric and port id is ethx/y -> reguylar port
        if node.isnumeric():
            path = get_mo_for_interface(str(row['NODE']), str(row['TARGET']))
            create_static_path(str(row['TENANT']), str(row['APP']), str(row['EPG']), path, str(row['VLAN']),
                               str(row['MODE']))
            print ("Adding -> Tenant: {0} - APP: {1} - EPG: {2} - LEAF: {3} - TARGET: {4} - ENCAP: {5} "
                   "- MODE: {6}".format(str(row['TENANT']),
                                        str(row['APP']), str(row['EPG']), str(row['NODE']), str(row['TARGET']),
                                        str(row['VLAN']), str(row['MODE'])))

        else:
            path = get_mo_for_pg(str(row['TARGET']))
            create_static_path(str(row['TENANT']), str(row['APP']), str(row['EPG']), path, str(row['VLAN']),
                               str(row['MODE']))
            print ("Adding -> Tenant: {0} - APP: {1} - EPG: {2} - LEAF: {3} - TARGET: {4} - ENCAP: {5} "
                   "- MODE: {6}".format(str(row['TENANT']),
                                        str(row['APP']), str(row['EPG']), str(row['NODE']), str(row['TARGET']),
                                        str(row['VLAN']), str(row['MODE'])))

moDir.logout()
