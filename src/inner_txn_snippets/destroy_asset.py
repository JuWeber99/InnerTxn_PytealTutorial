from pyteal import (InnerTxnBuilder, Seq, Subroutine, TealType, TxnField,
                    TxnType)


@Subroutine(TealType.none)
def inner_asset_destroy_txn(asset_id: TealType.uint64):
    """destroy an asset that is managed by the issuing contract"""
    return Seq([
        InnerTxnBuilder.Begin(),
        InnerTxnBuilder.SetFields({
            # This can only be performed if the sending application account
            #  is the manager of the ASA with asset_id and posseses the total amount of units!
            TxnField.type_enum: TxnType.AssetConfig,
            TxnField.config_asset: asset_id
            }),
        InnerTxnBuilder.Submit()
    ])
