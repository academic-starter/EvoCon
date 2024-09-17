import os
import json
import itertools
import numpy as np
import pandas as pd
import subprocess


def compareType(left, right, leftTypes, rightTypes):
    if "members" in left and "members" in right:
        left_members = left["members"]
        right_members = right["members"]
        for i in range(0, len(left_members)):
            left_member = left_members[i]
            right_member = right_members[i]

            if json.dumps(left_member) == json.dumps(right_member):
                continue
            try:
                left_member_type = leftTypes[left_member["type"]]
                right_member_type = rightTypes[right_member["type"]]

                left_member_name = left_member["label"]
                right_member_name = right_member["label"]

                type_match = compareType(
                    left=left_member_type, right=right_member_type, leftTypes=leftTypes, rightTypes=rightTypes)
                if not type_match:
                    return False, "struct-member type mismatches between {0}({1}) and {2}({3}) ".format(left_member_name, json.dumps(left_member_type), right_member_name, json.dumps(right_member_type))
                else:
                    if right_member_name.lower().find(left_member_name.lower()) == -1:
                        return False, "struct-member name largely mismatches between {0}({1}) and {2}({3}) ".format(left_member_name, json.dumps(left_member_type), right_member_name, json.dumps(right_member_type))
            except:
                continue

        return True, "type matches"

    elif left["encoding"] == "mapping" and right["encoding"] == "mapping":
        left_key_type = leftTypes[left["key"]]
        left_val_type = leftTypes[left["value"]]
        right_key_type = rightTypes[right["key"]]
        right_val_type = rightTypes[right["value"]]
        key_match = compareType(
            left_key_type, right_key_type, leftTypes=leftTypes, rightTypes=rightTypes)
        value_match = compareType(
            left_val_type, right_val_type, leftTypes=leftTypes, rightTypes=rightTypes)
        if key_match and value_match:
            return True, "type matches"
        else:
            if not key_match:
                return False, "mapping-key mismatches between {0} and {1} ".format(json.dumps(left_key_type), json.dumps(right_key_type))
            else:
                if not value_match:
                    return False, "mapping-value mismatches between {0} and {1} ".format(json.dumps(left_val_type), json.dumps(right_val_type))
                else:
                    assert False
    elif "members" not in left and "members" not in right and left["encoding"] != "mapping" and right["encoding"] != "mapping":
        type_match = json.dumps(left) == json.dumps(right)
        if type_match:
            return True, "type matches"
        else:
            return False, "type mismatches between {0} and {1}".format(json.dumps(left), json.dumps(right))
    else:
        return False, "type mismatches between {0} and {1}".format(json.dumps(left), json.dumps(right))


def test_pre_impl_storage_included_new_impl(pre_impl_storage, new_impl_storage):
    pre_storageLayout = pre_impl_storage["storageLayout"]
    new_storageLayout = new_impl_storage["storageLayout"]

    if pre_storageLayout is None or new_storageLayout is None:
        return True, "No storage layout specified"

    if not ("storage" in pre_storageLayout and "storage" in new_storageLayout):
        return True, "No storage layout specified"

    for i in range(len(pre_storageLayout["storage"])):
        pre_state_variable = pre_storageLayout["storage"][i]
        if i >= len(new_storageLayout["storage"]):
            return False, "Error: State variables {0} and onwards are removed".format(pre_state_variable["label"])
        new_state_variable = new_storageLayout["storage"][i]
        match, msg = compareType(
            pre_storageLayout["types"][pre_state_variable["type"]], new_storageLayout["types"][new_state_variable["type"]], pre_storageLayout["types"], new_storageLayout["types"])
        if not match:
            # if json.dumps(pre_storageLayout["types"][pre_state_variable["type"]]) != json.dumps(new_storageLayout["types"][new_state_variable["type"]]):
            return False, "Error: Type mismatch between {0}({1}) and {2}({3}); [detail]:{4}".format(pre_state_variable["label"], pre_state_variable["type"], new_state_variable["label"], new_state_variable["type"], msg)
        else:
            if new_state_variable["label"].lower().find(pre_state_variable["label"].lower()) != -1:
                pass
            else:
                return False, "Error: Name largely mismatch between {0}({1}) and {2}({3})".format(pre_state_variable["label"], pre_state_variable["type"], new_state_variable["label"], new_state_variable["type"])

    return True, "Storage layout remain compatible with previous storage"


def download_src_storage_layout(network, impl, artifact_file):
    export_dir = "evocon/contract_code/{0}".format(
        network)
    cmd = ""
    cmd += "bash evocon/analysis/scripts/download_src_storage_abi.sh {0} {1} {2} {3}".format(
        network,                                                                                   impl, export_dir, artifact_file)

    print(cmd)
    exitcode = os.system(cmd)
    print(exitcode)

    if os.path.exists(artifact_file):
        return json.load(open(artifact_file))
    else:
        return None


def load_storage_layout(network, impl, recompute=True):
    artifact_file = os.path.join(
        "evocon/contract_storage_layout", "{0}_{1}.json".format(network, impl.lower()))
    if impl == "0x0000000000000000000000000000000000000000" or impl == "0x0" or impl == "0x":
        return None
    if os.path.exists(artifact_file):
        return json.load(open(artifact_file))
    else:
        if recompute:
            return download_src_storage_layout(network=network, impl=impl, artifact_file=artifact_file)
        else:
            return None


def detect_storage_collision(chain):
    proxy_implementation_dir = "evocon/OnchainContractData/proxy_implementations/{0}_mainnet/".format(
        chain)

    cnt = 0
    blocks_results = {}
    impls_results = {}
    max_block = 0
    for item in os.listdir(proxy_implementation_dir):
        if item.endswith(".json"):
            address = item.split(".implementations.json")[0]
            result = json.load(
                open(os.path.join(proxy_implementation_dir, item)))
            if len(result) > 1:
                sorted_result = sorted(result, key=lambda x: x["block"])
                cnt += 1
                blocks = list(map(lambda x: x["block"], sorted_result))
                max_block = max([max_block, max(blocks)])
                blocks_results[address] = blocks

                impls = list(map(lambda x: x["implementation"], sorted_result))
                impls_results[address] = impls

    storage_collision_results = []
    for address in impls_results:
        cnt = 0
        pre_impl = None
        pre_impl_storage = None
        for new_impl in impls_results[address]:
            print(address, cnt, new_impl)

            new_impl_storage = load_storage_layout(chain,
                                                   new_impl, recompute=False)

            if pre_impl_storage is not None and new_impl_storage is not None:
                isIncluded, errorMsg = test_pre_impl_storage_included_new_impl(
                    pre_impl_storage, new_impl_storage)

                if not isIncluded:
                    storage_collision_results.append(
                        [address, str(cnt), str(cnt+1), pre_impl, new_impl,  errorMsg])

            pre_impl_storage = new_impl_storage
            pre_impl = new_impl
            # exit(0)
            cnt += 1

    print("=="*20)
    print("Summary:")
    print("Storage Collision results:", len(storage_collision_results))
    print("Details:", "\n".join([" ".join(item)
                                 for item in storage_collision_results]))

    json.dump(storage_collision_results, open(
        "evocon/analysis/{0}_storage_collision.json".format(chain), "w"), indent=4)


# "avalanche" used paid API plan
#  do not test it here
for chain in ["ethereum", "bsc", "arbitrum",
              "optimism", "polygon"]:
    print("------------------------")
    print("Chain: ", chain)
    print("------------------------")
    detect_storage_collision(chain=chain)
