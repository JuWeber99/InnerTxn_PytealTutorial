from pyteal import (Global, InnerTxnBuilder, Seq, Subroutine, TealType,
                    TxnField, TxnType)


@Subroutine(TealType.none)
def inner_payment_txn(amount: TealType.uint64, receiver: TealType.bytes):
    """casual payment transaction"""
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
