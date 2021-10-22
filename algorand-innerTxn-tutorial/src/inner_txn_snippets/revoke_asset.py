from pyteal import (InnerTxnBuilder, Seq, Subroutine, TealType, TxnField,
                    TxnType)


@Subroutine(TealType.none)
def inner_asset_clawback_txn(
    asset_id: TealType.uint64,
    asset_amount: TealType.uint64,
    clawback_addr: TealType.bytes,
    asset_receiver: TealType.bytes):
    """asset transfer using clawback workflow"""
    return Seq([
        InnerTxnBuilder.Begin(),
        InnerTxnBuilder.SetFields({
            TxnField.type_enum: TxnType.AssetTransfer,
            TxnField.xfer_asset: asset_id,
            TxnField.asset_amount: asset_amount,
            TxnField.asset_sender: clawback_addr,
            TxnField.asset_receiver: asset_receiver
            }),
        InnerTxnBuilder.Submit()
    ])
