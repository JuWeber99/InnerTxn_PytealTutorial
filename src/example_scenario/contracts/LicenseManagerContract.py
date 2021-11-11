
from pyteal import (Add, And, App, Approve, Assert, Balance, Btoi, Bytes,
                    BytesEq, Cond, Div, Global, Gtxn, If, Int, Minus, Mod,
                    Mode, Mul, Not, OnComplete, Reject, Return, Seq,
                    Subroutine, TealType, Txn, TxnType, compileTeal)
from pyteal.ast.asset import AssetHolding

from utils.InnerTxnUtils import (inner_payment_txn,
                                 inner_asset_creation, inner_asset_transfer)


class LocalState:
    """ wrapper class for access to predetermined Local State properties"""
    class Schema:
        """ Local State Schema """
        NUM_UINTS: TealType.uint64  = Int(2)
        NUM_BYTESLICES: TealType.uint64  = Int(0)

    class Variables:
        """ Local State Variables """
        STAKE_AMOUNT: TealType.bytes = Bytes("stakeAmount")
        LAST_STAKE_TIMESTAMP: TealType.bytes = Bytes("lastStakeTimestamp")


class GlobalState:
    """ wrapper class for access to predetermined Global State properties"""
    class Schema:
        """ Global State Schema """
        NUM_UINTS: TealType.uint64 = Int(3)
        NUM_BYTESLICES: TealType.uint64 = Int(0)
        

    class Variables:
        """ Global State Variables """
        FIXED_LICENSE_PRICE: TealType.bytes = Bytes("fixedLicensePrice")
        ASSET_ID: TealType.bytes = Bytes("assetID")
        REFUND_PERIOD: TealType.bytes = Bytes("refundPeriod")


class TxnTags:
    """ TxnTags for identification of intend """
    SETUP: TealType.bytes = Bytes("SETUP")
    ALGO_HANDIN: TealType.bytes = Bytes("ALGO_HANDIN")
    ASSET_HANDIN: TealType.bytes = Bytes("ASSET_HANDIN")


@Subroutine(TealType.uint64)
def is_valid_creation_call():
    """
    - validate the transactions are within security boundaries
    - validate the application create call is valid and sets up the ASA correctly
    """
    return Seq(
        Assert(Txn.type_enum() == TxnType.ApplicationCall),
        Assert(Txn.on_completion() == OnComplete.NoOp),
        # Matches the correct State Schema
        Assert(Txn.global_num_byte_slices() == GlobalState.Schema.NUM_BYTESLICES),
        Assert(Txn.global_num_uints() == GlobalState.Schema.NUM_UINTS),
        Assert(Txn.local_num_byte_slices() == LocalState.Schema.NUM_BYTESLICES),
        Assert(Txn.local_num_uints() == LocalState.Schema.NUM_UINTS),
        Int(1))


@Subroutine(TealType.uint64)
def is_valid_setup_call(fund_txn_index: TealType.uint64, app_call_txn_index: TealType.uint64):
    """
    - validate the transactions are within security boundaries
    - validate the application create call is valid and sets up the ASA correctly
    """
    return Seq(
        # first transaction is seeding the application account
        Assert( Gtxn[fund_txn_index].type_enum() == TxnType.Payment ),
        # you can calculate the min balance you need here ... I just sent 400k to have enough for playing around
        Assert( Gtxn[fund_txn_index].amount() >= Int(400000) ),
        Assert( Gtxn[app_call_txn_index].type_enum() == TxnType.ApplicationCall ),
        Assert( Gtxn[app_call_txn_index].on_completion() == OnComplete.NoOp ),
        # if the application is yet to be created the application ID will be 0
        Assert( Gtxn[app_call_txn_index].application_id() != Int(0) ),
        # the correct amount of application_args are specified since the call whould later fail elsewhise anyways
        Assert( Gtxn[app_call_txn_index].application_args.length() == Int(8) ),
        Int(1))

@Subroutine(TealType.uint64)
def buy_licenses(payment_txn_index: TealType.uint64, asset_id: TealType.uint64):
    """ perform the operation to buy licenses """
    # first transaction in thr group should be the buy payment
    buyer_payment_txn = Gtxn[payment_txn_index]
    amount_sent = buyer_payment_txn.amount()
    fixed_asset_price = getFixedAssetPrice()
    # how many assets can be bought wth the provided amount of microAlgo
    bought_asset_amount = Div(amount_sent, fixed_asset_price)
    # determine if there is rest resulting out of the Modulo operation over
    # the sent amount of microAlgos and
    # the fixed asset price
    refund_amount = Mod(amount_sent, fixed_asset_price)
    new_stake = Mul(bought_asset_amount, fixed_asset_price)

    return Seq(
        #  check if the payment is enough to buy even 1 unit
        If(bought_asset_amount > Int(0)).Then(
            # if so transfer the bought units
            inner_asset_transfer(
                asset_id,
                bought_asset_amount,
                Global.current_application_address(),
                buyer_payment_txn.sender())
            ),
        # check if the buyer maybe sent 1100 microAlgos but the price is 1000
        # so he payed 100 microAlgos too much
        # (in real world scenario care that its worth to refund
        # since it should be at least 1k microAlgos because of transaction costs)
        If(refund_amount > Int(0)).Then(
            inner_payment_txn(refund_amount, buyer_payment_txn.sender())
        ),
        # update local state
        App.localPut(buyer_payment_txn.sender(), LocalState.Variables.STAKE_AMOUNT, new_stake),
        App.localPut(
            buyer_payment_txn.sender(),
            LocalState.Variables.LAST_STAKE_TIMESTAMP,
            Global.latest_timestamp()),
        Int(1))

@Subroutine(TealType.uint64)
def is_valid_license_buy_call(
    app_call_txn_index: TealType.uint64,
    algo_hand_in_txn_index: TealType.uint64,
    asset_id: TealType.uint64,
    fixed_asset_price: TealType.uint64
    ):
    """ check if txn is within security boundaries and a valid buying call"""
    # the first transaction sends the microAlgos to pay for the ASA units
    algo_hand_in_txn = Gtxn[algo_hand_in_txn_index]
    # the application call just triggers the correct application logic
    app_call_txn = Gtxn[app_call_txn_index]
    return Seq(
        # if buyer isn´t opted-in failure is inevitable
        Assert( is_acc_opted_in(app_call_txn.sender()) ),
        Assert( app_call_txn.type_enum() == TxnType.ApplicationCall ),
        Assert( app_call_txn.on_completion() == OnComplete.NoOp ),
        Assert( algo_hand_in_txn.type_enum() == TxnType.Payment ),
        Assert( app_call_txn.sender() ==  algo_hand_in_txn.sender() ),
        # correct asset gets sent
        Assert( app_call_txn.assets[0] == asset_id ),
        # enough money sent to buy at least 1 unit
        Assert( algo_hand_in_txn.amount() >= fixed_asset_price ),
        Int(1))


@Subroutine(TealType.uint64)
def refund_bought_licenses():
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


@Subroutine(TealType.uint64)
def is_valid_refund_call():
    """ check if txn is within security boundaries """
    asset_return_amount = Btoi(Txn.application_args[0])
    fixed_asset_price = getFixedAssetPrice()
    asset_id = getAssetId()
    refund = Mul(asset_return_amount, fixed_asset_price)
    current_staked_amount = getStakedAmount(Txn.sender())
    return Seq(
        Assert( is_acc_opted_in(Txn.sender()) ),
        Assert( Txn.on_completion() == OnComplete.NoOp ),
        # buyer returns at least 1 unit thus the calculated refund is bigger or equal to the price
        Assert( refund >= fixed_asset_price ),
        # if he hasnt event the stake to pay the refund something is wrong
        Assert( current_staked_amount >= refund ),
        # buyer tries to return the correct asset
        Assert( Txn.assets[0] == asset_id ),
        Int(1))


@Subroutine(TealType.uint64)
def is_acc_opted_in(account: TealType.bytes):
    return App.optedIn(account, Global.current_application_id())


@Subroutine(TealType.uint64)
def setup_application( ):
    """ perform application setup to initiate global state and create the managed ASA"""
    asset_id = inner_asset_creation(Int(1))
    fixed_license_price = Btoi(Gtxn[1].application_args[6])
    refund_period = Btoi(Gtxn[1].application_args[7])
    return Seq(
        # initiate Global State
        App.globalPut(
            GlobalState.Variables.FIXED_LICENSE_PRICE,
            fixed_license_price),
        App.globalPut(GlobalState.Variables.ASSET_ID, asset_id),
        App.globalPut(GlobalState.Variables.REFUND_PERIOD, refund_period),
        Int(1))


@Subroutine(TealType.uint64)
def is_allegible_for_refund():
    """ check if allegible for refund """
    passed_seconds = Minus(Global.latest_timestamp(), getLastStakeTimestamp(Txn.sender()))
    return ( passed_seconds <= getRefundPeriod() )


@Subroutine(TealType.uint64)
def close_out():
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

# --- Global Getters ---
@Subroutine(TealType.uint64)
def getAssetId():
    """ Getter for GlobalState.ASSET_ID """
    return App.globalGet(GlobalState.Variables.ASSET_ID)


@Subroutine(TealType.uint64)
def getFixedAssetPrice():
    """ Getter for GlobalState.FIXED_ASSET_PRICE """
    return App.globalGet(GlobalState.Variables.FIXED_LICENSE_PRICE)


@Subroutine(TealType.uint64)
def getRefundPeriod():
    """ Getter for GlobalState.FIXED_ASSET_PRICE """
    return App.globalGet(GlobalState.Variables.REFUND_PERIOD)

# --- Local Getters ---

@Subroutine(TealType.uint64)
def getStakedAmount(account: TealType.bytes):
    """ Getter for LocalState.FIRST_STAKE_ROUND """
    return App.localGet(account, LocalState.Variables.STAKE_AMOUNT)


@Subroutine(TealType.uint64)
def getLastStakeTimestamp(account: TealType.bytes):
    """ Getter for LocalState.FIRST_STAKE_ROUND """
    return App.localGet(account, LocalState.Variables.LAST_STAKE_TIMESTAMP)

# --- Approval Program ---

def approval_program():
    """approval program for the contract"""

    # App Lifecycle
    handle_closeout_lifecycle = And(
        is_acc_opted_in(Txn.sender()), # if account isn´t opted in failure is imminent
        close_out())
    handle_app_creation_lifecycle = is_valid_creation_call() 
    handle_deleteapp_lifecycle =  Int(0) # we don´t want that top happen in this example
    handle_clear_state_lifecycle = Int(0) # we don´t want that to happen in this example
    handle_optin_lifecycle = Int(1) # allow everyone to opt-in

# Dev Operation
    setup_app_operation = And(
        is_valid_setup_call(Int(0), Int(1)),
        setup_application())

# business logic operations
    on_license_buy_operation = And(
        is_valid_license_buy_call(
            Int(1),
            Int(0),
            getAssetId(),
            getFixedAssetPrice()),
        buy_licenses(Int(0), getAssetId()))

    refund_operation = And(
        is_valid_refund_call(),
        refund_bought_licenses())

# Main Conditional
    program = Cond(
        # Check the group_size() first since if wrong, we dont even have to start
        [ Global.group_size () == Int(1),
            Cond(
                [ Txn.application_id() == Int(0), Return(handle_app_creation_lifecycle) ],
                [ BytesEq(Txn.note(), TxnTags.ASSET_HANDIN), Return(refund_operation)],
                [ Txn.on_completion() == OnComplete.DeleteApplication, Return(handle_deleteapp_lifecycle) ],
                [ Txn.on_completion() == OnComplete.ClearState, Return(handle_clear_state_lifecycle) ],
                [ Txn.on_completion() == OnComplete.OptIn, Return(handle_optin_lifecycle) ],
                [ Txn.on_completion() == OnComplete.CloseOut, Return(handle_closeout_lifecycle) ])],
        [ Global.group_size() == Int(2),
            Cond(
                # like above the note gets checked to determine the intend of the call
                [ BytesEq(Gtxn[1].note(), TxnTags.SETUP), Return(setup_app_operation) ],
                [ BytesEq(Gtxn[1].note(), TxnTags.ALGO_HANDIN), Return(on_license_buy_operation) ])],
        [ Global.group_size() >= Int(2), Reject() ]
    )

    return program


with open('innerTxn_tutorial_pyteal.teal', 'w', encoding="UTF-8") as f:
    COMPILED_PROGRAM = compileTeal(approval_program(), Mode.Application, version=5)
    f.write(COMPILED_PROGRAM)
