from pyteal import InnerTxnBuilder, TxnField, Seq, TealType, Subroutine, TxnObject, And, Int, ImportScratchValue, Assert, Cond, TxnExpr, Bytes, Assert, App, TxnType, Reject, Global, compileTeal, Mode, Expr



########################## AUSSORTIEREN!!!!!! ##############################
@Subroutine(TealType.uint64)
def refundValidation(callID: TealType.uint64, appID: TealType.uint64, refundTxn: TxnObject):
    Assert(refundTxn.type_enum() == TxnType.Payment)
    isCorrectReceiver = App.localGetEx(
        refundTxn.receiver, appID, Bytes("isHighestBidder")) == Int(1)
    refundAmount = ImportScratchValue(callID, 10)
    return And(refundTxn.amount == refundAmount,
               isCorrectReceiver)


@Subroutine(TealType.uint64)
def highestBidPaymentValidation(appID: TealType.uint64, paymentTxn: TxnObject):
    Assert(paymentTxn.type_enum() == TxnType.Payment)
    highestBid = App.globalGetEx(appID, Bytes("highestBid"))
    return paymentTxn.amount == highestBid


def newHighestBidValidation(appID: TealType.uint64, paymentTxn: TxnObject, refundTxn: TxnObject, appCallIndex: TealType.uint64 = 1):
    areBaseChecksValid = And(validatePaymentBaseParams(refundTxn),
                             validatePaymentBaseParams(paymentTxn))
    belongsToCorrectAuction = originAuctionValidation(appID, appCallIndex)
    # TODO can soonTM be done with inner Transaction
    isRefundValid = refundValidation(appID, appCallIndex, refundTxn)
    isPaymentAmountCorrect = highestBidPaymentValidation(appID, paymentTxn)
    return And(
        areBaseChecksValid,
        belongsToCorrectAuction,
        isRefundValid,
        isPaymentAmountCorrect
    )


def sellerPayoutValidation(appID: TealType.uint64,
                           assetSellerAddress: TealType.bytes,
                           paymentTxn: TxnObject,
                           appCall: TxnObject):
    # TODO can soonTM be done with inner Transaction (so just abondon sender check)
    Assert(paymentTxn.type_enum() == TxnType.Payment)
    isCorrectReceiver = paymentTxn.receiver == assetSellerAddress
    isCalledWithCorrectApplication = appCall.application_id == appID
    Assert(App.globalGetEx(appID, Bytes("isAuctionClosed") == Int(1)))
    return And(isCorrectReceiver, isCalledWithCorrectApplication)


@Subroutine(TealType.uint64)
def validatePaymentBaseParams(txn: TxnObject):
    txnCloseTo = txn.close_remainder_to
    txnRekeyTo = txn.rekey_to
    txnFee = txn.fee
    isValidCloseToAddress = txnCloseTo == Global.zero_address()
    isValidRekeyToAddress = txnRekeyTo == Global.zero_address()
    isFeeInLimits = txnFee < Int(1000)
    return And(
        isValidCloseToAddress,
        isValidRekeyToAddress,
        isFeeInLimits)


@Subroutine(TealType.uint64)
def assetXferParameterValidation(assetTransferTxn: TxnObject, assetID, auctionedAmount, assetSellerAddress):
    isCorrectAsset = assetTransferTxn.xfer_asset() == assetID
    isCorrectAssetAmount = assetTransferTxn.amount == auctionedAmount
    isCorrectAssetSender = assetTransferTxn.sender == assetSellerAddress
    return And(
        isCorrectAsset,
        isCorrectAssetAmount,
        isCorrectAssetSender
    )


@Subroutine(TealType.uint64)
def assetXferReceiverValidation(asset_receiver: TxnExpr, appID: TealType.uint64, key=Bytes("isAuctionWinner")):
    auctionWonState = App.localGetEx(asset_receiver, appID, key)
    return And(
        auctionWonState.hasValue(),
        auctionWonState == Int(1))


@Subroutine(TealType.uint64)
def auctionEndedValidation(appID: TealType.uint64):
    # and minDuration passed
    return App.globalGetEx(appID, Bytes("isAuctionClosed")) == Int(1)


@Subroutine(TealType.uint64)
def originAuctionValidation(appCall: TxnObject, appID: TealType.uint64):
    return appCall.application_id() == appID


def validateAssetPayoutTxn(assetTransferTxn: TxnObject, appCall: TxnObject, appID: TealType.uint64, assetID: TealType.uint64, assetSellerAddress: TealType.bytes, auctionedAssetAmount: TealType.uint64):
    """
        1.) are the base parameters for the transactions set correct (rekey and close-to-adress + is belonging to correct app + is the fee ok?)
        2.) is the auction closed
        3.) is it an AssetTransferTxn
        4.1.1 ) is it the correct sender
        4.1.2 ) does he want to send the correct asset
        4.2.1 ) is the asset transfer receiver correct
        4.2.2 ) has he the localState isAuctionWinner set and it is 1 (he won the auction)
    """
    Assert(assetTransferTxn.type_enum() == TxnType.AssetTransfer)
    Assert(appCall.type_enum() == TxnType.ApplicationCall)
    # areBaseChecksValid = validatePaymentBaseParams(
    #   assetTransferTxn.asset_close_to(),
    #   assetTransferTxn.rekey_to(),
    #   assetTransferTxn.fee()
    # )
    belongsToCorrectAuction = originAuctionValidation(
        appCall.application_id, appID)
    didAssetChecksPass = assetXferParameterValidation(
        assetTransferTxn, assetID, auctionedAssetAmount, assetSellerAddress)
    isAuctionClosed = auctionEndedValidation(appID)
    isValidReceiver = assetXferReceiverValidation(
        assetTransferTxn.asset_receiver, appID)

    return And(
        # areBaseChecksValid,
        belongsToCorrectAuction,
        didAssetChecksPass,
        isAuctionClosed,
        isValidReceiver
    )
