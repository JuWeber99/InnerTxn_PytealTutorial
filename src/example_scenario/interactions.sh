#!/bin/bash

app_creator="XZ4QB6VE3KL4ZNOPB77KZTCOJNSXKAYZQQ2CSWKQCEV7ZO7ACQVPOLHCJI"
client="WXX535OGAPIBZ7QQU2BJWSP3F4ZV4OGHDI7WXOHBTIODJARMKVE3WRIHWI"

unit_name="ROW"
asset_name="ALICE1"
decimals=0
price=1000
total_amount=100
url="http://ipfs_url"
metadata_hash="AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA" #placeholder value


refund_period=1

# to debug use smth like: tealdbg debug -d <dryrun_dump.txn> -v --remote-debugging-port 9392 --listen "" -a <appid>


#create app
function create_app {
    goal app create --clear-prog innerTxn_tutorial_pyteal.teal --approval-prog innerTxn_tutorial_pyteal.teal --local-byteslices 0 --local-ints 2 --global-ints 3 --global-byteslices 0 --creator $app_creator | grep 'Created app' | awk '{print $6}'
}


function setup_app {
    #setup app and create asset
    goal app call -n "SETUP" --app-id "$app_id" --app-arg "str:$metadata_hash" \
        --app-arg "str:$asset_name" --app-arg "str:$unit_name" --app-arg "int:$total_amount" \
        --app-arg "int:$decimals" --app-arg "str:$url" --app-arg "int:$price" \
        --app-arg "int:$refund_period" --out setup_txn.txn --from $app_creator 
    goal clerk send --from="$app_creator" --to="$app_addr" --amount=400000 --out paycontractsustain.txn 
    cat paycontractsustain.txn setup_txn.txn > combined.txn
    goal clerk group -i combined.txn -o group_txn_setup.txn 
    goal clerk split -i group_txn_setup.txn -o splitted.txn 
    goal clerk sign -i splitted-0.txn -o signout-0.txn 
    goal clerk sign -i splitted-1.txn -o signout-1.txn && cat signout-0.txn signout-1.txn > setup.txn
    goal clerk dryrun -t setup.txn -o setup.debug --dryrun-dump
    goal clerk rawsend -f setup.txn
}

function retrieve_asset_info {
    goal app read --app-id $app_id --global | grep 'ui' | head -n 1 | awk -F ": " '{print $2}'
}

function optin_routine {
    # opt into ASA and Smart Contract
    goal asset send -a 0 --assetid $asset_id  -f $client -t $client --creator $app_addr
    goal app optin --app-id "$app_id" --from "$client"
    goal app optin --app-id "$app_id" --from "$client"  --dryrun-dump --out app_optin_txn 
}


function algo_handin {
    # algo hand in - VALID
    goal app call --app-id "$app_id" --from "$client" --note "ALGO_HANDIN" --foreign-asset $asset_id  \
     --app-account $app_addr --out algo_in_app_1.txn 
    goal clerk send --from="$client" --to="$app_addr" --amount=18000  --out algohandin.txn
    cat algohandin.txn algo_in_app_1.txn > combined_handin.txn 
    goal clerk group -i combined_handin.txn -o group_txn_handin.txn 
    goal clerk split -i group_txn_handin.txn -o splitted_handin.txn 
    goal clerk sign -i splitted_handin-0.txn -o signout_handin-0.txn 
    goal clerk sign -i splitted_handin-1.txn -o signout_handin-1.txn 
    cat signout_handin-0.txn signout_handin-1.txn > handin.txn 
    goal clerk dryrun -t handin.txn -o handin.debug --dryrun-dump --dryrun-accounts "$app_addr"
    goal clerk rawsend -f handin.txn
    echo " ----------- ALGO HANDIN FROM BUYER SUCESSFUL ----------- "
}

function asset_handin {
    # asset hand in - VALID
    ret_amount=10
    goal app call --app-id "$app_id" --from "$client" --note "ASSET_HANDIN" --foreign-asset $asset_id  \
     --app-account $app_addr --app-arg "int:$ret_amount" 
    echo " ----------- ASSSET HANDIN FROM BUYER SUCESSFUL ----------- "
}


function invalid_algo_handin {
    echo " TESTING INVALID ALGO HANDIN TXN .... "
    # algo hand in - INVALID NOTE TEST 
    goal app call --app-id "$app_id" --from "$client" --note "ALGO_HANDI" --foreign-asset $asset_id  \
     --app-account $app_addr --out algo_in_app_2.txn 
    goal clerk send --from="$client" --to="$app_addr" --amount=18000  --out algohandin2.txn
    cat algohandin2.txn algo_in_app_2.txn > combined_handin2.txn 
    goal clerk group -i combined_handin2.txn -o group_txn_handin2.txn 
    goal clerk split -i group_txn_handin2.txn -o splitted_handin2.txn 
    goal clerk sign -i splitted_handin2-0.txn -o signout_handin2-0.txn 
    goal clerk sign -i splitted_handin2-1.txn -o signout_handin2-1.txn 
    cat signout_handin2-0.txn signout_handin2-1.txn > handin2.txn 
    goal clerk dryrun -t handin2.txn -o handin2.debug --dryrun-dump --dryrun-accounts "$app_addr"
    test_txn=$(goal clerk rawsend -f handin2.txn) 
    test=$(echo $test_txn | grep error)
    if [[ $test ]]
        then
            echo "----------- INVALIDITY SUCESSFULLY COMFIRMED -----------"
        else
            echo $invalid_test
    fi
}

function issued_asset_aamt {
    goal asset info --assetid $asset_id  | grep Issued | tr -d " " | awk -F ":" '{print $2}'
}

function closeout {
    goal app closeout --from $client --app-id $app_id --foreign-asset $asset_id
}

app_id=$(create_app)
app_addr=$(goal app info --app-id $app_id | grep 'Application account' | awk '{print $3}')
echo "App Address: $app_addr"
setup_app && \
asset_id=$(retrieve_asset_info) && \
echo "AssetID: $asset_id" && \
optin_routine && \
algo_handin
echo "----------"
echo "Outstanding client balance: $(issued_asset_aamt)"
sleep 2
asset_handin
echo "----------"
echo "Outstanding client balance: $(issued_asset_aamt)"
#invalid_algo_handin
closeout
echo "----------"   
echo "Outstanding client balance: $(issued_asset_aamt)"