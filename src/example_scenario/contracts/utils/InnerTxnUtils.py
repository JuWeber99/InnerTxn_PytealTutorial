from pyteal import (Btoi, Bytes, Expr, Global, Gtxn, InnerTxnBuilder, Int, Seq,
                    Subroutine, TealType, TxnExpr, TxnField, TxnType)
from pyteal.ast.itxn import InnerTxn


@Subroutine(TealType.uint64)
def inner_asser_creation(txn_index: TealType.uint64) -> TxnExpr:
    """
    - returns the id of the generated asset or fails
    """
    call_parameters = Gtxn[txn_index].application_args
    asset_total = Btoi(call_parameters[3])
    decimals = Btoi(call_parameters[4])
    return Seq([
        InnerTxnBuilder.Begin(),
        InnerTxnBuilder.SetFields({
            TxnField.note: Bytes("TUT_ITXN_AC"),
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


@Subroutine(TealType.none)
def inner_asset_transfer(asset_id: TealType.uint64, asset_amount: TealType.uint64, asset_sender: TealType.bytes, asset_receiver: TealType.bytes) -> Expr:
    return Seq([
        InnerTxnBuilder.Begin(),
        InnerTxnBuilder.SetFields({
            TxnField.note: Bytes("TUT_ITXN_AT"),
            TxnField.type_enum: TxnType.AssetTransfer,
            TxnField.xfer_asset: asset_id,
            TxnField.asset_sender: asset_sender,
            TxnField.asset_amount: asset_amount,
            TxnField.asset_receiver: asset_receiver
            }),
        InnerTxnBuilder.Submit()
    ])


@Subroutine(TealType.none)
def inner_payment_txn(amount: TealType.uint64, receiver: TealType.bytes) -> Expr:
    return Seq([
        InnerTxnBuilder.Begin(),
        InnerTxnBuilder.SetFields({
            TxnField.note: Bytes("TUT_ITXN_PAY"),
            TxnField.type_enum: TxnType.Payment,
            TxnField.sender: Global.current_application_address(),
            TxnField.amount: amount,
            TxnField.receiver: receiver
            }),
        InnerTxnBuilder.Submit()
    ])
