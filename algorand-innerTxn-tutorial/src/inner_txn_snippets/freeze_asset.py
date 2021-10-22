from pyteal import (InnerTxnBuilder, Int, Seq, Subroutine, TealType,
                    TxnField, TxnType)


@Subroutine(TealType.none)
def inner_asset_freeze_txn(asset_id: TealType.uint64, address_to_freeze_for: TealType.bytes):
    """freeze an asset for an account"""
    freeze = Int(1)
   # unfreeze = Int(0)
    return Seq([
        InnerTxnBuilder.Begin(),
        InnerTxnBuilder.SetFields({
            # This can only be performed if the sending application account
            #  is the Freeze manager of the ASA with asset_id!
            TxnField.type_enum: TxnType.AssetFreeze,
            TxnField.freeze_asset: asset_id,
            TxnField.freeze_asset_frozen: freeze, # or unfreeze
            TxnField.freeze_asset_account: address_to_freeze_for
            }),
        InnerTxnBuilder.Submit()
    ])
