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


exclusion_int_po = [
    {
        "leaf": 101,
        "target_list": ["eth1/10"]
    },
    {
        "leaf": 102,
        "target_list": ["eth1/1"]
    }

]

exclusion_vpc = ["Heroes_FI-2"]


def matched_excluded_vpc(pg_name):
    for key in exclusion_vpc:
        if key == pg_name:
            return True


def matched_excluded_int_po(leaf, target_int):
    for key in exclusion_int_po:
        if key["leaf"] == leaf:
            for key2 in key["target_list"]:
                if key2 == target_int:
                    return True


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


# Exclusion verification
print("Parsing CSV file and checking whether we are requesting changes on excluded int/po/vpc ...")
with open('Test.csv') as csvfile:
    reader = csv.DictReader(csvfile, delimiter=';')
    for row in reader:
        node = unicode(row['NODE'])
        target = str(row['TARGET'])
        if node.isnumeric():
            if matched_excluded_int_po(int(row['NODE']), target):
                exit("Found excluded line in CSV : {0} {1}".format(node, target))
        elif matched_excluded_vpc(target):
            exit("Found excluded line in CSV for VPC : {0}".format(target))
print ("Exclusion verification : [DONE]")

moDir = apic_logon('https://sandboxapicdc.cisco.com', 'admin', 'password')
with open('Test.csv') as csvfile:
    reader = csv.DictReader(csvfile, delimiter=';')
    for row in reader:
        # Checking whether it is regular port or PC/VPC
        node = unicode(row['NODE'])
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
