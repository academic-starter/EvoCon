import os
import json
import itertools
import re
import glob

from matplotlib import pyplot as plt
from matplotlib_venn import venn3


BLOCKCHAIN_MP = {
    1: "ethereum",
    10: "optimism",
    56: "bsc",
    137: "polygon",
    250: "fantom",
    8453: "base",
    42161: "arbitrum",
    43114: "avalanche"
}
src_db_files = glob.glob(os.path.join("usccheck/analysis/dappproject",
                         "dappproject-*.json"))
source_code_db_map = dict()

pattern = re.compile("dappproject-([0-9]*).json")
for src_db_file in src_db_files:
    m = pattern.match(os.path.basename(src_db_file))
    if m is None:
        continue
    chain_id = int(m.groups()[0])
    chain_name = BLOCKCHAIN_MP[chain_id]
    source_code_db_map[chain_name] = json.load(open(src_db_file))

abi_found = {}


def load_contract_abi(chain, impl):
    global abi_found
    if impl == "0x0000000000000000000000000000000000000000" or impl == "0x0" or impl == "0x":
        return None
    if chain == "ethereum":
        abi_file = os.path.join(
            "/Users/yeliu/Projects/USCCheck/usccheck/contract_abi", impl.lower()+".abi.json")
        if os.path.exists(abi_file):
            arr = abi_found.get(chain, set())
            arr.add(impl)
            abi_found[chain] = arr
            return json.load(open(abi_file))
        else:
            assert chain in source_code_db_map
            src_db = source_code_db_map[chain]
            contract_items = list(
                filter(lambda x: x["address"] == impl, src_db))
            if len(contract_items) == 0:
                return None
            contract_item = contract_items[0]
            abi = contract_item["abi"]
            arr = abi_found.get(chain, set())
            arr.add(impl)
            abi_found[chain] = arr
            return abi
    else:
        assert chain in source_code_db_map
        src_db = source_code_db_map[chain]
        contract_items = list(
            filter(lambda x: x["address"].lower() == impl.lower(), src_db))
        if len(contract_items) == 0:
            return None
        contract_item = contract_items[0]
        abi = contract_item["abi"]
        arr = abi_found.get(chain, set())
        arr.add(impl)
        abi_found[chain] = arr
        return abi


def detect_for_chain_dapp(db):
    import re
    pattern = re.compile("dappproject-([0-9]+).upgrade.json")
    m = pattern.match(os.path.basename(db))
    chain_id = int(m.groups()[0])
    chain_name = BLOCKCHAIN_MP[chain_id]
    print("--------------------------------")
    print("Chain: " + chain_name)
    print("--------------------------------")
    data = json.load(open(db))
    ABI_breaking_change_function_removal = []
    ABI_breaking_change_function_parameter_update = []
    ABI_breaking_change_function_returns_update = []
    for dapp_id in data:
        migrations = data[dapp_id]
        cnt = 0
        for migration in migrations:
            migration_dir = os.path.join(
                src_db_dir, chain_name, dapp_id, str(cnt))
            if not os.path.exists(migration_dir):
                os.makedirs(migration_dir)
            old_contract_item = migration["old"]
            new_contract_item = migration["new"]
            prev_impl = old_contract_item["address"]
            new_impl = new_contract_item["address"]

            cnt += 1

            prev_impl_abi = load_contract_abi(chain_name, prev_impl)
            new_impl_abi = load_contract_abi(chain_name, new_impl)

            if prev_impl_abi is not None and new_impl_abi is not None:
                # calculate function removals
                for abi_function in prev_impl_abi:
                    if abi_function["type"] == "function":
                        abi_function_name = abi_function["name"]
                        if not any([_abi_func["name"] == abi_function_name for _abi_func in new_impl_abi if _abi_func["type"] == "function"]):
                            ABI_breaking_change_function_removal.append(
                                [dapp_id, new_impl, prev_impl, abi_function])

                # calculate function parameter modifications
                for abi_function in prev_impl_abi:
                    if abi_function["type"] == "function":
                        abi_function_name = abi_function["name"]
                        abi_function_signature = abi_function_name + \
                            "(" + ",".join([_input["type"]
                                            for _input in abi_function["inputs"]])+")"

                        abi_function_parameters = [_input["name"]
                                                   for _input in abi_function["inputs"]]
                        if any([_abi_func["name"] == abi_function_name for _abi_func in new_impl_abi if _abi_func["type"] == "function"]):

                            if not any([_abi_func["name"]+"(" + ",".join([_input["type"]
                                                                          for _input in _abi_func["inputs"]])+")" == abi_function_signature for _abi_func in new_impl_abi if _abi_func["type"] == "function"]):
                                ABI_breaking_change_function_parameter_update.append(
                                    [dapp_id, new_impl, prev_impl, abi_function])
                            else:
                                for _abi_func in new_impl_abi:
                                    if _abi_func["type"] == "function":
                                        if abi_function_signature == _abi_func["name"]+"(" + ",".join([_input["type"]
                                                                                                       for _input in _abi_func["inputs"]])+")":
                                            new_abi_function_parameters = [_input["name"]
                                                                           for _input in _abi_func["inputs"]]
                                            if set(abi_function_parameters) == set(new_abi_function_parameters) and new_abi_function_parameters != abi_function_parameters:
                                                # parameter order changes
                                                print("parameter order changes:", abi_function_name,
                                                      abi_function_parameters, "->", new_abi_function_parameters)
                                                ABI_breaking_change_function_parameter_update.append(
                                                    [dapp_id, new_impl, prev_impl, abi_function])

                # calculate function return types modifications
                for abi_function in prev_impl_abi:
                    if abi_function["type"] == "function":
                        abi_function_name = abi_function["name"]
                        abi_function_signature = abi_function_name + \
                            "(" + ",".join([_input["type"]
                                            for _input in abi_function["inputs"]])+")"
                        abi_function_signature_outputs = abi_function_signature + "(" + ",".join([_output["type"]
                                                                                                  for _output in abi_function["outputs"]])+")"
                        if any([_abi_func["name"] == abi_function_name for _abi_func in new_impl_abi if _abi_func["type"] == "function"]):

                            if any([_abi_func["name"]+"(" + ",".join([_input["type"]
                                                                      for _input in _abi_func["inputs"]])+")" == abi_function_signature for _abi_func in new_impl_abi if _abi_func["type"] == "function"]):
                                if not any([_abi_func["name"]+"(" + ",".join([_input["type"]
                                                                              for _input in _abi_func["inputs"]])+")" + "(" + ",".join([_output["type"] for _output in _abi_func["outputs"]])+")" == abi_function_signature_outputs for _abi_func in new_impl_abi if _abi_func["type"] == "function"]):

                                    ABI_breaking_change_function_returns_update.append(
                                        [dapp_id, new_impl, prev_impl, abi_function])

    print("================================")
    print("Summary:")
    print(" ABI breaking changes-removal of functions: ",
          len(ABI_breaking_change_function_removal))
    print(" ABI breaking changes-update of function parameters: ",
          len(ABI_breaking_change_function_parameter_update))
    print(" ABI breaking changes-modification of function return types: ",
          len(ABI_breaking_change_function_returns_update))

    dapp_function_removal = set(
        [item[0] for item in ABI_breaking_change_function_removal])
    dapp_parameter_update = set(
        [item[0] for item in ABI_breaking_change_function_parameter_update])
    dapp_returns_update = set(
        [item[0] for item in ABI_breaking_change_function_returns_update])
    print("================================")
    print("Summary:")
    print("[dapp_id] ABI breaking changes-removal of functions: ",
          len(dapp_function_removal))
    print("[dapp_id] ABI breaking changes-update of function parameters: ",
          len(dapp_parameter_update))
    print("[dapp_id] ABI breaking changes-modification of function return types: ",
          len(dapp_returns_update))
    print("[dapp_id] ABI breaking changes (unique): ",
          len(dapp_returns_update.union(dapp_parameter_update).union(dapp_function_removal)))

    migrate_function_removal = set(
        [(item[0], item[1], item[2]) for item in ABI_breaking_change_function_removal])
    migrate_parameter_update = set(
        [(item[0], item[1], item[2]) for item in ABI_breaking_change_function_parameter_update])
    migrate_returns_update = set(
        [(item[0], item[1], item[2]) for item in ABI_breaking_change_function_returns_update])
    print("================================")
    print("Summary:")
    print("[Migrate] ABI breaking changes-removal of functions: ",
          len(migrate_function_removal))
    print("[Migrate] ABI breaking changes-update of function parameters: ",
          len(migrate_parameter_update))
    print("[Migrate] ABI breaking changes-modification of function return types: ",
          len(migrate_returns_update))

    print("[Migrate] ABI breaking changes (unique): ",
          len(migrate_returns_update.union(migrate_parameter_update).union(migrate_function_removal)))

    # Set font properties
    # Use Times New Roman or similar serif font
    plt.rcParams['font.family'] = 'serif'
    plt.rcParams['font.size'] = 18  # Adjust font size as needed

    # Create the Venn diagram
    venn = venn3([dapp_function_removal, dapp_parameter_update, dapp_returns_update],
                 ('Function\nremoval', 'Parameter\nupdate', 'Return\nchange'), set_colors=("orange", "blue", "red"), alpha=0.5)

    # # Display the plot
    # # plt.title('ABI breaking changes in the implemenation of proxy contracts')
    # plt.show()

    # Output the results to a file
    plt.savefig(
        'usccheck/analysis/dappproject/ABI_breaking_changes-{0}.pdf'.format(chain_name), format='pdf')

    # close the plot
    plt.close()

    print("Found ABI for {0} contracts".format(
        len(abi_found.get(chain_name, []))))


src_db_dir = os.path.dirname(__file__)
all_dbs = glob.glob(os.path.join(src_db_dir, "dappproject-*.upgrade.json"))

for db in all_dbs:
    detect_for_chain_dapp(db)
