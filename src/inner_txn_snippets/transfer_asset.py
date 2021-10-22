from pyteal import (InnerTxnBuilder, Seq, Subroutine, TealType, TxnField,
                    TxnType)


@Subroutine(TealType.none)
def inner_asset_transfer_txn(
    asset_id: TealType.uint64,
    asset_amount: TealType.uint64,
    asset_receiver: TealType.bytes):
    """casual asset transfer"""
    return Seq([
        InnerTxnBuilder.Begin(),
        InnerTxnBuilder.SetFields({
            TxnField.type_enum: TxnType.AssetTransfer,
            TxnField.xfer_asset: asset_id,
            TxnField.asset_amount: asset_amount,
            TxnField.asset_receiver: asset_receiver
            }),
        InnerTxnBuilder.Submit()
    ])