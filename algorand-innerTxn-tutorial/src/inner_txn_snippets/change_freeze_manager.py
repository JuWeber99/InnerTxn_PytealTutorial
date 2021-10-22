from pyteal import (InnerTxnBuilder, Seq, Subroutine, TealType, TxnField,
                    TxnType)


@Subroutine(TealType.none)
def inner_asset_freeze_manager_change_txn(asset_id: TealType.uint64, new_freeze_manager: TealType.bytes):
    """change the freeze manager"""
    return Seq([
        InnerTxnBuilder.Begin(),
        InnerTxnBuilder.SetFields({
            # This can only be performed if the sending application account
            #  is the manager of the ASA with asset_id!
            TxnField.type_enum: TxnType.AssetConfig,
            TxnField.config_asset: asset_id,
            TxnField.config_asset_freeze: new_freeze_manager,
            }),
        InnerTxnBuilder.Submit()
    ])
