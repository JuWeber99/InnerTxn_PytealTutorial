
# Requirements

- Basic knowledge about Algorand and blockchain technologies
- Basic knowledge about PyTeal development
- Basic understanding of Smart Contracts on Algorand
- PyTEAL version supporting TEAL v5
- Algorand sandbox



# 1. Inner Transaction Fundamentals

In this tutorial i want to introduce you to a new feature that came with the update to AVM1.0: **Inner Transactions**.

**Inner Transactions** enable Stateful Smart Contracts to perform their on transactions. These transactions are performed by on-chain logic and so empower Stateful Smart Contracts to encapsulate much more logic on-chain and away from your centralized backend application logic. 
In this way more of the logic actually performed in Usecases using Algorand can be transparently governed and secured by the blockchain itself. 

Consulting to the Docs you can find the structure of each type of transaction here: https://developer.algorand.org/docs/get-details/transactions
Look there to make sure you understand the structure of the **inner transactions** you want to send and you chose the right structure for your **InnerTransaction**.

With this function for example, a simple payment transaction can be issued:

```
@Subroutine(TealType.none)
def inner_payment_txn(amount: TealType.uint64, receiver: TealType.bytes) -> Expr:
    return Seq([
        InnerTxnBuilder.Begin(),
        InnerTxnBuilder.SetFields({
            TxnField.type_enum: TxnType.Payment,
            TxnField.sender: Global.current_application_address(),
            TxnField.amount: amount,
            TxnField.receiver: receiver
            }),
        InnerTxnBuilder.Submit()
    ])
```
**Inner Transaction** in PyTEAL always start with a c followed by setting the fields with either `InnerTxnBuilder.SetField()` one by one or setting all fields in one function with `InnerTxnBuilder.SetFields()`.
In an **Inner Transaction** you created the context of with `InnerTxnBuilder.Begin()` all fields that get not set by `InnerTxnBuilder.SetField()` or `InnerTxnBuilder.SetFields()` are automatically set to **zero-values**. 
On the `InnerTxnBuilder.Begin()` instruction the *sender* of the transaction gets automatically set to `Global.current_application_address()` since only the contract itself can authorize to send an **Inner Transaction**. The `FirstValid` and the 'LastValid' values of the **Inner Transaction** will be set to the values of the **wrapping** application call. Last but not least the the fees for the **Inner Transaction** gets set to the *minimum fee* possible also with fee-overpaying from earlier transactions taken into consideration.
Finally the transaction can be executed via `InnerTxnBuilder.Submit()`. It fails if already **16** **Inner Transaction** have been submitted in the block or the transaction itself fails. You can also access the *ID* of the newly create **ASA** on sucessful execution of the Inner Transaction by using the: `InnerTxn.created_asset_id()` instruction right after the submit. This will also be again shown in the *Example Scenario*

On the Algorand Dev Portal you can find a great introduction to **Inner Transactions**: https://developer.algorand.org/docs/get-details/dapps/smart-contracts/apps/?from_query=inner%20tra#inner-transactions

# 2. Example Scenario Concept


To demonstrate the usefulness of Inner Transactions the article uses an Example Scenario utilizing *PyTEAL*.

There will be a Smart Contract which functions like an Asset-Manager as the only one being able to transfer units of the asset using clawback transactions. 
For simplicities sake the Asset Manager just gives away a certain amount X of the ASA for Y amount of microAlgo
This resolves to the following example:

A creator *Alice* wants to sell a *license* which enables the holder to rightfully republish or use something she is the originator of.
She wants to sell a certain amount of the licenses on chain. Therefore *Alice* can create a *LicenseManagerContract* for her licenses and tokenizes them as **ASA**. 
She could use a full fletched dApp which abstracts the technical aspects of the process away for that. 
To stay with the essence I will leave it to the reader if he wants to try and create his own dApp using the contract to stay by the main intend of the article.

![EditorImages/2021/10/22 17:47/Screenshot_2021-10-22_at_19.47.09.png](https://algorand-devloper-portal-app.s3.amazonaws.com/static/EditorImages/2021/10/22%2017%3A47/Screenshot_2021-10-22_at_19.47.09.png) 
![EditorImages/2021/10/22 17:37/Screenshot_2021-10-22_at_19.36.05.png](https://algorand-devloper-portal-app.s3.amazonaws.com/static/EditorImages/2021/10/22%2017%3A37/Screenshot_2021-10-22_at_19.36.05.png)

# 2.1 Overview over the Approval Program

Overview over the approval program: 
```
 program = Cond(
        [ Global.group_size () == Int(1),
            Cond(
                [ Txn.application_id() == Int(0), Return(create_app) ],
                [ BytesEq(Txn.note(), TxnTags.ASSET_HANDIN), Return(perform_asset_hand_in)],
                [ Txn.on_completion() == OnComplete.DeleteApplication, Return(handle_deleteapp) ],
                [ Txn.on_completion() == OnComplete.ClearState, Return(handle_clear_state) ],
                [ Txn.on_completion() == OnComplete.OptIn, Return(handle_optin) ],
                [ Txn.on_completion() == OnComplete.CloseOut, Return(handle_closeout) ])],
        [ Global.group_size() == Int(2),
            Cond(
                [ BytesEq(Gtxn[1].note(), TxnTags.SETUP), Return(setup_app) ],
                [ BytesEq(Gtxn[1].note(), TxnTags.ALGO_HANDIN), Return(on_algo_hand_in) ])],
        [ Global.group_size() >= Int(2), Reject() ]
    )
```

# 2.2 Creating the Contract

_Alice_ creates the contract with the **goal SDK**:

```
#create app
function create_app {
    app_id=$(goal app create --clear-prog innerTxn_tutorial_pyteal.teal \
     --approval-prog innerTxn_tutorial_pyteal.teal \
     --local-byteslices 0 \
     --local-ints 1 \
     --global-ints 2 \
     --global-byteslices 0 \
     --creator $app_creator | grep 'Created app' | awk '{print $6}')
    echo "AppID: $app_id"
}
```

The app here basically just checks if is not already created thus has an application id of 0.
Also it checks the application  and the state schema was specified correctly  for this app sinceit has to have 2 local uint Variables (`STAKED_AMOUNT`, `LAST_STAKE_ROUND`)
and **3 global uint** variables (`FIXED_LICENSE_PRICE`, `ASSET_ID`, `REFUND_PERIOD`)
for the application state and it that its a single transaction with on completion code: **NoOp**. 

The `STAKED_AMOUNT` keeps track of the payed in *microAlgos* by the buyer.
The `STAKED_AMOUNT` determines the amount of *microAlgos* a user can receive as a maximum. 
Based on it, the refund amount `Y` can be calculated and refunded to the buyer in exchange for `X` amount **ASA** units if he wants so. 
`Y` whould be the result out of the following:



* `REFUND=X * FIXED_LICENSE_PRICE`. 

After doing that the `STAKED_AMOUNT` will get substracted by the refund: `STAKED_AMOUNT=STAKED_AMOUNT-REFUND`.
The `REFUND_PERIOD` is a value of seconds and no Asset handin after the refund period: 


* `Global.latest_timestamp() - LAST_STAKE_TIMESTAMP <= REFUND_PERIOD`,

gets any part of `STAKE_AMOUNT` back.
If the call to give back assets happens after the refund_period the buyer gets no Algos back and can´t give the units back.
If he buys more licenses the refund of the previous buy will be obsolet.
Warning! For simplicities sake the handling of Edge Cases regarding abuse prevention is may not complete and security checks are missing!

# 2.3 Setting up the Contract

Now ... as the contract is created on the blockchain and *Alice* can setup it up for her needs. 
She wants now to set the price per license to **1000** *microAlgo* and the total amount of licenses to **100**. 
She names the asset and the units of it and links data on ipfs via the url, to link a file containing another visually showable proof. 
Also she can set a refund period. The refund period specifies the time a buyer is allegible to give back license units and get his algo back 

```
price=1000
total_amount=100
decimals=0
asset_name="ALICE1"
unit_name="ROW"
url="http://ipfs_url"
metadata_hash="AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA" # placeholder value

#refund_period=584000 # approx. 1 month on real network
refund_period=1 # approx. q round = 4,5 seconds on a real network


```

Then she just needs to call the *LicenseManagerContract* with the settings she wants to use as arguments to perform the setup of the smart contract.
But before we need to make sure to seed the account with microAlgos.
To ensure this happens safely we just group a payment transaction at **group index 0** to seed the app together with the application call to setup the app at **group index 1**.
Below you can see how the goal commands for each transaction look. 
In the Github Repo you can find all the code used ...and more, with comments!


* https://github.com/JuWeber99/InnerTxn_PytealTutorial/
```
    # seed app 
    goal clerk send --from="$app_creator" --to="$app_addr" --amount=400000 
    
    # setup call
    goal app call -n "SETUP" --app-id "$app_id" --app-arg "str:$metadata_hash" \
        --app-arg "str:$asset_name" --app-arg "str:$unit_name" --app-arg "int:$price" \
        --app-arg "int:$decimals" --app-arg "str:$url" --app-arg "int:$total_amount" \
        --out setup_txn.txn --from $app_creator 
```

The app will do some checks and if they are passed the app will issue an inner transaction to create an asset with the specified app arguments from the setup call

```
@Subroutine(TealType.uint64)
def setup_application( ):
    """ perform application setup """
    asset_id = executeAssetCreationTxn(Int(1))
    ...
```

To create a new **ASA** via **Inner Transaction** there needs to be a function performing an *AssetConfiguration* transaction with the different `config_asset` -
parameters being set in the transaction using the app arguments specified by *Alice* in the **Application Call**.

```
@Subroutine(TealType.uint64)
def executeAssetCreationTxn(txn_index: TealType.uint64) -> TxnExpr:
    """
     returns the ID of the generated asset or fails
    """
    call_parameters = Gtxn[txn_index].application_args
    asset_total = Btoi(call_parameters[3])
    decimals = Btoi(call_parameters[4])
    return Seq([
        InnerTxnBuilder.Begin(),
        InnerTxnBuilder.SetFields({
            TxnField.type_enum: TxnType.AssetConfig,
            TxnField.config_asset_clawback: Global.current_application_address(),
            TxnField.config_asset_reserve: Global.current_application_address(),
            TxnField.config_asset_default_frozen: Int(1),
            TxnField.config_asset_metadata_hash: call_parameters[0],
            TxnField.config_asset_name: call_parameters[1],
            TxnField.config_asset_unit_name: call_parameters[2],
            TxnField.config_asset_total: asset_total,
            TxnField.config_asset_decimals: decimals,
            TxnField.config_asset_url: call_parameters[5],
        }),
        InnerTxnBuilder.Submit(),
        InnerTxn.created_asset_id()
    ])
```

When this code gets sucessfully executed, the resulting block can be inspected by using `goal ledger block`.
Like this its easy to check if the **Inner Transactions** looks like `Alice` wants:

```
"itx": [
            {
              "caid": 312,
              "txn": {
                "apar": {
                  "am:b64": "QUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUE=",
                  "an": "ALICE1",
                  "au": "http://ipfs_url",
                  "c:b64": "Gi6iTWtyp/KxfPPtFzovVRqUnjtIhVQs5aZurXGnVtk=",
                  "df": true,
                  "r:b64": "Gi6iTWtyp/KxfPPtFzovVRqUnjtIhVQs5aZurXGnVtk=",
                  "t": 100,
                  "un": "ROW"
                },
                "fee": 1000,
                "fv": 146,
                "lv": 1146,
                "snd:b64": "Gi6iTWtyp/KxfPPtFzovVRqUnjtIhVQs5aZurXGnVtk=",
                "type": "acfg"
              }
            }
          ]
```

And again checking against: https://developer.algorand.org/docs/get-details/transactions/#create-an-asset ...
It looks like it indeed is correct!

The InnerTransaction can also pass back the *ID* of the newly created **ASA** back to the program.
This can be used to safe the *ID* of newly created assed instantly to the global state. 
The asset id can be returned by returning `InnerTxn.created_asset_id()`. 
We can even set a note for the **Inner Transaction**!

You can see this in the rest of the setup_application - subroutine
``` 
    ...

    return Seq(
        App.globalPut(
            GlobalState.Variables.FIXED_ASSET_PRICE,
            fixed_license_price),
        App.globalPut(GlobalState.Variables.ASSET_ID, asset_id),
        App.globalPut(GlobalState.Variables.REFUND_PERIOD, refund_period),
        Int(1))
```

Now *Alice* can´t wait to check if it worked since her transaction got sucessfully comitted!
She checks out the asset id through reading the global state value of her created contract 
```
goal app read --app-id $app_id --global | grep 'ui' | head -n 1 | awk -F ": " '{print $2}'
```
There she sees the asset id and checks if everything has gone well...
```
goal asset info --assetid $asset_id 
```
Yes! Everything is ready and the selling can start! :
```
Asset ID:         268
Creator:          KXBPX6NQODNRCXGVMSWS3HPAI66B22OT5QZEUD2BEE2QR5ESWXYOKMTLRE
Asset name:       ALICE1

Unit name:        ROW

Maximum issue:    100 ROW
Reserve amount:   100 ROW
Issued:           0 ROW
Decimals:         0
Default frozen:   true
Manager address:
Reserve address:  KXBPX6NQODNRCXGVMSWS3HPAI66B22OT5QZEUD2BEE2QR5ESWXYOKMTLRE
Freeze address:
Clawback address: KXBPX6NQODNRCXGVMSWS3HPAI66B22OT5QZEUD2BEE2QR5ESWXYOKMTLRE
```

# 2.4 Opting into the Contract

_Bob_ just runs the optin routine to opt-into the **ASA** and the **LicenseManagerContract**: 
 ```
function optin_routine {
    # opt into ASA and Smart Contract
    goal asset send -a 0 --assetid $asset_id  -f $client -t $client --creator $app_addr
    goal app optin --app-id "$app_id" --from "$client"
    goal app optin --app-id "$app_id" --from "$client"  --dryrun-dump --out app_optin_txn 
}
 ```

# 2.5 Buying licenses 

*Bob* gets a call from *Alice* that he now can as promised buy licenses from her on the Algorand Blockchain.
He opens the aforementioned mysterious dApp in his browser and now wants to buy some licenes for 18000 microAlgos!

Therefore Bob has to group the Application Call to call the **LicenseManagerContract** with his payment transaction over 18000 microAlgos to the contract. 

```
    ...
        Assert( acc_opted_in(app_call_txn.sender()) ),
        Assert( app_call_txn.type_enum() == TxnType.ApplicationCall ),
        Assert( app_call_txn.on_completion() == OnComplete.NoOp ),
        Assert( algo_hand_in_txn.type_enum() == TxnType.Payment ),
    ...
```

Again, both single transactions whould look like this using the goal SDK:

```
goal app call --app-id "$app_id" --from "$client" --note "ALGO_HANDIN" --foreign-asset $asset_id  \
     --app-account $app_addr --out algo_in_app_1.txn 

goal clerk send --from="$client" --to="$app_addr" --amount=18000  

```

As *Bobs* Transaction group gets sucessfully send to the contract, the contract executes the logic assigned to `on_algo_hand_in`, because of the note and the group size.

```
 [ Global.group_size() == Int(2),
            Cond(
                [ BytesEq(Gtxn[1].note(), TxnTags.ALGO_HANDIN), Return(on_algo_hand_in) ])]
            ...
```

After the security checks happened, the **LicenseManagerContract** sets the `STAKE_AMOUNT` to the amount of microAlgo that where paid in exchange for an asset. 
Since the `FIXED_LICENSE_PRICE` is **1000** *Bob* gets **18** units of *Alice´s* **ASA** thus: `ASA_HANDOUT_AMOUNT=ALGO_HANDIN_AMOUNT / FIXED_LICENSE_PRICE` .
The `LAST_STAKE_TIMESTAMP` where *Bobs* transaction got successfully committed will be set to the value of the `latest_timestamp`.

```
return Seq(
        App.localPut(algo_hand_in_txn.sender(), LocalState.Variables.STAKE_AMOUNT, new_stake),
        App.localPut(algo_hand_in_txn.sender(), LocalState.Variables.LAST_STAKE_TIMESTAMP, Global.latest_timestamp()),
        ...
```

Then the new feature for **InnerTransactions** comes in very handy yet again!
The contract finally can send the **18** units if the **ASA** to *Alice* using an inner transaction if the `asset_amount` whould be greater than 0. 

```
If(asa_handout_amount > Int(0)).Then(
            executeAssetTransfer(
                asset_id,
                asa_handout_amount,
                Global.current_application_address(),
                algo_hand_in_txn.sender())
            ) ...
```

Therefore simply specify the **InnerTransaction** again. After, like everytime the InnerTxnBuilder begins, the necassary fields are set to their value via the `SetFields` function to perform this action for multiple fields in one function, passing a python - key-value mapping.
Since the asset transfer is performed everytime and only by the contract itself, using a clawback transacttion, the asset_sender must be set to the address of the **LicenseManagerContract** itself. The asset_amount whould be the aforementioned `ASA_HANDOUT_AMOUNT` (**18**). 


```
@Subroutine(TealType.none)
def executeAssetTransfer(asset_id: TealType.uint64, asset_amount: TealType.uint64, asset_sender: TealType.bytes, asset_receiver: TealType.bytes) -> Expr:
    return Seq([
        InnerTxnBuilder.Begin(),
        InnerTxnBuilder.SetFields({
            TxnField.type_enum: TxnType.AssetTransfer,
            TxnField.xfer_asset: asset_id,
            TxnField.asset_sender: asset_sender,
            TxnField.asset_amount: asset_amount,
            TxnField.asset_receiver: asset_receiver
            }),
        InnerTxnBuilder.Submit()
    ])
```

Now if *Bob* has send more *microAlgos* so that there is a rest of the division when calculating `ASA_HANDOUT_AMOUNT`, the rest amount of microAlgos get send back to *Bob*.
Therefore the simple inner payment function from the beginning can be used, specifying how much *microsAlgo* to send to which **receiver**:

```
...
If(refund_amount > Int(0)).Then(
            inner_payment_txn(refund_amount, algo_hand_in_txn.sender())
        )
...
```

Now *Bob* wants to check if all went well and he got the units of *Alice´s* **ASA**:



* `goal account info -a "$client"`

He can see all the **ASAs** he has with their **ID**, **asset name**, **unit name** and **balance**.

*Bob* is glad as everything seems to have worked correctly:


* `ID 302, ALICE1, balance 18 ROW (frozen)`


# 2.6 Request a refund for ASA

Now whats left is to discover the refund mechanism and the closeout logic.
If Bob decides before the refund period ends he can, as already described above, get back a part of his stake or even everything on full refund.
He knows the exact time he has to refund via the **global state value**:`REFUND_PERIOD` so he is obliged to check it correctly because he can´t refund and cant give back the units as beforehand aggreed with *Alice* 

```
@Subroutine(TealType.uint64)
def handle_asset_hand_in():
    """ handler for asset to algo logic """
    fixed_asset_price = getFixedAssetPrice()
    asset_return_amount = Btoi(Txn.application_args[0])
    refund_amount = Mul(asset_return_amount, fixed_asset_price)
    current_staked_amount = getStakedAmount(Txn.sender())
    updated_stake = Minus(current_staked_amount, refund_amount)
    
    return Seq(
        # if is refund period still active then refund
        If(is_allegible_for_refund()).Then(
            Seq(
                inner_asset_transfer(
                getAssetId(),
                asset_return_amount,
                Txn.sender(),
                Global.current_application_address()),
                inner_payment_txn(refund_amount, Txn.sender()),
                # update STAKE_AMOUNT
                App.localPut(
                    Txn.sender(),
                    LocalState.Variables.STAKE_AMOUNT, updated_stake),
                # the call gets approved
                Int(1))
        # Else the call gets rejected
        ).Else(Int(0)))
```

To now execute a refund action *Bob* will use following bash-function utilizing the *goal SDK* :

```
function asset_handin {
    # asset hand in - VALID
    ret_amount=10
    goal app call --app-id "$app_id" --from "$client" --note "ASSET_HANDIN" --foreign-asset $asset_id  \
     --app-account $app_addr --app-arg "int:$ret_amount" 
    echo " ----------- ASSSET HANDIN FROM BUYER SUCESSFUL ----------- "
}
```

Now if he did this correctly in the refund period, he can perform the refund. 
Since transactions are very cheap on Algorand *Bob* decides to try if this really works.
He instantly performs the above bash-function instantly after the buying action to give back **10** units of his **18** bought licence units.

He now checks is the transactions are really executed as they should be and looks at the block with the newly created transaction hash: 


* `goal ledger block $block_round` (see in output of the `goal app call`-command -> e.g. committed in round 144)

```
    "txns": [
      {
        "dt": {
          "itx": [
            {
              "txn": {
                "aamt": 10,
                "arcv:b64": "Gi6iTWtyp/KxfPPtFzovVRqUnjtIhVQs5aZurXGnVtk=",
                "asnd:b64": "IlnKUR/5avzx8pAlphB4XXtr+b2V7/5SX9J6Q3j/Tos=",
                "fee": 1000,
                "fv": 150,
                "lv": 1150,
                "snd:b64": "Gi6iTWtyp/KxfPPtFzovVRqUnjtIhVQs5aZurXGnVtk=",
                "type": "axfer",
                "xaid": 312
              }
            },
            {
              "txn": {
                "amt": 10000,
                "fee": 1000,
                "fv": 150,
                "lv": 1150,
                "rcv:b64": "IlnKUR/5avzx8pAlphB4XXtr+b2V7/5SX9J6Q3j/Tos=",
                "snd:b64": "Gi6iTWtyp/KxfPPtFzovVRqUnjtIhVQs5aZurXGnVtk=",
                "type": "pay"
              }
            }
          ],
```

*Bob* sees that he indeed got **10000** *microAlgos* via **Inner Transaction** in the `itxn - Array` the the above output:

```
txn": {
                "amt": 10000,
                "fee": 1000,
                "fv": 150,
                "lv": 1150,
                "rcv:b64": "IlnKUR/5avzx8pAlphB4XXtr+b2V7/5SX9J6Q3j/Tos=",
                "snd:b64": "Gi6iTWtyp/KxfPPtFzovVRqUnjtIhVQs5aZurXGnVtk=",
                "type": "pay"
        }
```

.. and of course the **10 ASA units** were also withrdrawn from his account:

```
"txn": {
                "aamt": 10,
                "arcv:b64": "Gi6iTWtyp/KxfPPtFzovVRqUnjtIhVQs5aZurXGnVtk=",
                "asnd:b64": "IlnKUR/5avzx8pAlphB4XXtr+b2V7/5SX9J6Q3j/Tos=",
                "fee": 1000,
                "fv": 150,
                "lv": 1150,
                "snd:b64": "Gi6iTWtyp/KxfPPtFzovVRqUnjtIhVQs5aZurXGnVtk=",
                "type": "axfer",
                "xaid": 312
        }
```

# 2.7 Close out of the Contract

Last but not least *Bob* could **Close Out** of the **LicenseManagerContract** by sending an **Application Call** with a **OnCompletion** value of **CloseOut**. 
This will on success result in a handin of the whole balance of *ASA units* which have the **ASSET_ID** managed by the **LicenseManagerContract** (stored in its global state).
If the **CloseOut**-Call happens before the end of the refund period *Bob* whould get his `STAKED_AMOUNT` of *microAlgos* refunded.
Else, he will just turn all the ** ASA units ** he posseses in whithout a reward.

```
@Subroutine(TealType.uint64)
def handle_close_out_txn():
    """ closeout-txn handler """

    asset_id = getAssetId()
    current_staked_amount = App.localGet(Txn.sender(), LocalState.Variables.STAKE_AMOUNT)
    sender_asset_balance = AssetHolding.balance(Txn.sender(), Int(0))

    return Seq(
        # if refund period active send refund
        If(is_allegible_for_refund()).Then(
            inner_payment_txn(current_staked_amount, Txn.sender() ),
        ),
        # check if the sender of the closeout even has units of the ASA
        sender_asset_balance,
        If(And(sender_asset_balance.hasValue(), sender_asset_balance.value() > Int(0))).
        Then(
            # if so revoke them from the sender closing out of the LicenseManagerContract
            inner_asset_transfer(
                asset_id,
                sender_asset_balance.value(),
                Txn.sender(),
                Global.current_application_address())),
        # Clear the Local State of the sender closing out
        App.localDel(Txn.sender(), LocalState.Variables.STAKE_AMOUNT),
        App.localDel(Txn.sender(), LocalState.Variables.LAST_STAKE_TIMESTAMP),
        Int(1)) 
```

If *Bob* after handing back in **10** of his **18 ASA units** now issues a closing out call:

*  `goal app closeout --from $client --app-id $app_id --foreign-asset $asset_id`

and then checks if he has no **ASA units left now**:

*  `goal account info -a "$client"` 

... he now sees (Note! The IDs will probably be different for you so I shortened the output):



* `ALICE1, balance 0 ROW (frozen)`


If `Bob` checks the block created out of the successful `CloseOut` transaction and the `CloseOut`was performed after the `REFUND_PERIOD` was over, he will sadly have to accept that his stake is now once and for all *Alice´s* since there is no **Inner Transaction** performed by the **LicenseManagerContract** to send the refund after the `REFUND_PERIOD` :

```
"itx": [
            {
              "txn": {
                "aamt": 18,
                "arcv:b64": "JeW54j2iSsLpCFBoWk4sR8zTgXWIP2BOunNbyLpOH6A=",
                "asnd:b64": "te/d9cYD0Bz+EKaCm0n7LzNeOMcaP2u44ZocNIIsVUk=",
                "fee": 1000,
                "fv": 13,
                "lv": 1013,
                "snd:b64": "JeW54j2iSsLpCFBoWk4sR8zTgXWIP2BOunNbyLpOH6A=",
                "type": "axfer",
                "xaid": 19
              }
            }
          ],
```

# 3. Conclusion

In my opinion, the ability to perform transactions from on-chain logic will bring a new dynamic to the developement of the Ecosystem since it enables creator to think out the concepts for their desired project in a more straight-forward way. Currently `AssetFreeze, AssetConfiguration, AssetTransfer and Payment` *Transaction-Types* are supported for performing **Inner Transactions**. If this article sparked your interest you can also see more *PyTEAL* snippets for inner transactions of different kinds each got an extra file so you dont have to scroll inside one big file!
A bright future is ahead for even a bigger empowerement of capabilities of the *TEAL* - Language since the *Algorand Dev team* is also looking into providing the possibility to perform `Application Call` transactions using **Inner Transactions**: https://github.com/algorand/go-algorand/pull/3120
