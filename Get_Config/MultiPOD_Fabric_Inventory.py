from cobra.mit.session import LoginSession
from cobra.mit.access import MoDirectory
from cobra.mit.request import ClassQuery
# from cobra.mit.naming import Dn
from prettytable import PrettyTable
import requests.packages.urllib3

requests.packages.urllib3.disable_warnings()


def apic_logon(url, username, password):
    my_session = LoginSession(url, username, password)
    modir_local = MoDirectory(my_session)
    modir_local.login()
    return modir_local


def apic_logoff():
    moDir.logout()


def get_pod_list():
    cq = ClassQuery('fabricPod')
    result = moDir.query(cq)
    return result


def get_leaf_by_pod(pod_id):
    nodes = moDir.lookupByClass("fabricNode", parentDn=pod_id.dn)
    list_leaf = []
    for x in nodes:
        if x.role == "leaf":
            # print x.dn
            list_leaf.append(x)
    return list_leaf


def get_int_per_leaf(leaf):
    ports = moDir.lookupByClass("l1PhysIf", parentDn=leaf.dn)
    return ports


def get_int_link_state(port):
    query = moDir.lookupByClass("ethpmPhysIf", parentDn=port)
    return query[0].operSt


def process_int_by_leaf(port_list):
    total_ep_port_count = 0
    total_fab_port_count = 0
    total_epg_port_count = 0
    total_blacklist_count = 0
    total_unconfigured_count = 0
    total_up_ep_port = 0
    total_down_ep_port = 0
    epg_port_mode = ('epg', 'controller,epg,infra', 'blacklist,epg')

    for port in port_list:
        state = get_int_link_state(port.dn)

        # Count Downlinks port and check their Link Status
        if port.portT == "leaf":
            total_ep_port_count += 1
            if state == "up":
                total_up_ep_port += 1
            elif state == "down":
                total_down_ep_port += 1

        if port.portT == "fab":
            total_fab_port_count += 1
        if port.portT == "leaf" and port.usage in epg_port_mode:
            total_epg_port_count += 1
        if port.portT == "leaf" and port.usage == "blacklist,epg":
            total_blacklist_count += 1
        if port.portT == "leaf" and port.usage == "discovery":
            total_unconfigured_count += 1
    percent_provisionned = total_epg_port_count * 100 / total_ep_port_count
    return (total_ep_port_count, total_fab_port_count, total_epg_port_count, total_blacklist_count,
            percent_provisionned, total_up_ep_port, total_down_ep_port)


moDir = apic_logon('https://sandboxapicdc.cisco.com', 'admin', 'password')

pod_list = get_pod_list()
pod_count = len(pod_list)

print ("Number of POD(s) : {0}".format(pod_count))

for pod in pod_list:
    print ("POD {0} :".format(pod.id))
    table = PrettyTable()
    table.field_names = ["Leaf Name", "Model", "Serial", "Downlinks (total)", "Uplinks (capacity)",
                         "Downlinks Configured", "Downlinks Blacklisted", "% Occupation Downlinks", "Downlinks Link Up",
                         "Downlinks Link Down"]
    leaf_list = get_leaf_by_pod(pod)

    for element in leaf_list:
        port_list1 = get_int_per_leaf(element)
        tmp, tmp2, tmp3, tmp4, tmp5, tmp6, tmp7 = process_int_by_leaf(port_list1)
        # print ("{0} -- Model: {1} -- DownLinks ({2}) -- Uplinks ({3}) \n"
        #        "Downlinks: Configured ({4}) - Blacklisted ({5}) - Occupation ({6}%) \n"
        #        "Downlinks: LinkUp ({7}) - LinkDown ({8})"
        #        .format(element.name, element.model, tmp, tmp2, tmp3, tmp4, tmp5, tmp6, tmp7))

        table.add_row([element.name, element.model, element.serial, tmp, tmp2, tmp3, tmp4, tmp5, tmp6, tmp7])
    print (table)

# leaf_result = get_leaf_by_pod(pod_list[0])
# get_int_per_leaf(leaf_result[0])
apic_logoff()
