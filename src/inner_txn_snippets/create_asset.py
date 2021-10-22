
from pyteal import (Btoi, Global, Gtxn, InnerTxn, InnerTxnBuilder, Int, Seq,
                    Subroutine, TealType, TxnField, TxnType)


@Subroutine(TealType.uint64)
def inner_assert_creation_txn(txn_index: TealType.uint64):
    """
    create ASA with provided AppArgs and return the id of the generated asset (or fail)
    """
    # get your application call arguments supposed to be the AssetParams of the asset to create
    call_parameters = Gtxn[txn_index].application_args
    # --- for example: ---
    asset_name= call_parameters[0]
    unit_name= call_parameters[1]
    # attention to convert the needed arguments to the right type!
    total_amount= Btoi(call_parameters[2])
    url= call_parameters[3]
    decimals = Btoi(call_parameters[4])
    metadata_hash= call_parameters[5] #placeholder value

    return Seq([
        InnerTxnBuilder.Begin(),
        InnerTxnBuilder.SetFields({
            TxnField.type_enum: TxnType.AssetConfig,
            TxnField.config_asset_clawback: Global.current_application_address(),
            TxnField.config_asset_reserve: Global.current_application_address(),
            # creating the asset default frozen without zeroed manager address
            TxnField.config_asset_default_frozen: Int(1),
            TxnField.config_asset_name: asset_name,
            TxnField.config_asset_unit_name: unit_name,
            TxnField.config_asset_total: total_amount,
            TxnField.config_asset_url: url,
            TxnField.config_asset_decimals: decimals,
            TxnField.config_asset_metadata_hash: metadata_hash,
        }),
        InnerTxnBuilder.Submit(),
        # return the ID of the created ASA from the subroutine for further use
        InnerTxn.created_asset_id()
    ])
