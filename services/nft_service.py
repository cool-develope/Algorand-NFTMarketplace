from typing import Dict

from algosdk.v2client import algod
from algosdk import logic as algo_logic
from algosdk.future import transaction as algo_txn
from pyteal import compileTeal, Mode
from algosdk.encoding import decode_address

from utils.transaction import (
    ApplicationTransactionRepository,
    ASATransactionRepository,
    PaymentTransactionRepository,
)
from utils.network import NetworkInteraction
from smart_contracts.nft_contract import NFTContract


class NFTService:
    def __init__(
            self,
            nft_creator_address: str,
            nft_creator_pk: str,
            client: algod.AlgodClient,
            nft_info: Dict
    ):
        self.creator_pk = nft_creator_pk
        self.creator_address = nft_creator_address
        
        self.client = client

        self.nft_info = nft_info

        self.teal_version = 4
        self.nft_marketplace_asc1 = NFTContract()

        self.app_id = None
        self.nft_id = None

    @property
    def escrow_bytes(self):
        if self.app_id is None:
            raise ValueError("App not deployed")

        escrow_fund_program_compiled = compileTeal(
            NFTContract.nft_escrow(app_id=self.app_id, asa_id=self.nft_id),
            mode=Mode.Signature,
            version=self.teal_version,
        )

        return NetworkInteraction.compile_program(
            client=self.client, source_code=escrow_fund_program_compiled
        )

    @property
    def escrow_address(self):
        return algo_logic.address(self.escrow_bytes)

    def create_nft(self):
        signed_txn = ASATransactionRepository.create_non_fungible_asa(
            client=self.client,
            creator_private_key=self.creator_pk,
            unit_name=self.nft_info.get("unit_name"),
            asset_name=self.nft_info.get("asset_name"),
            note=self.nft_info.get("description"),
            manager_address=self.creator_address,
            reserve_address=self.creator_address,
            freeze_address=self.creator_address,
            clawback_address=self.creator_address,
            url=self.nft_info.get("url"),
            default_frozen=True,
            sign_transaction=True,
        )

        nft_id, tx_id = NetworkInteraction.submit_asa_creation(
            client=self.client, transaction=signed_txn
        )
        self.nft_id = nft_id
        return tx_id

    def change_nft_credentials_txn(self):
        txn = ASATransactionRepository.change_asa_management(
            client=self.client,
            current_manager_pk=self.creator_pk,
            asa_id=self.nft_id,
            manager_address="",
            reserve_address="",
            freeze_address="",
            strict_empty_address_check=False,
            clawback_address=self.escrow_address,
            sign_transaction=True,
        )

        tx_id = NetworkInteraction.submit_transaction(self.client, transaction=txn)

        return tx_id

    def opt_in(self, account_pk):
        opt_in_txn = ASATransactionRepository.asa_opt_in(
            client=self.client, sender_private_key=account_pk, asa_id=self.nft_id
        )

        tx_id = NetworkInteraction.submit_transaction(self.client, transaction=opt_in_txn)
        return tx_id

    def app_initialization(self, nft_owner_address):
        approval_program_compiled = compileTeal(
            self.nft_marketplace_asc1.approval_program(),
            mode=Mode.Application,
            version=self.teal_version,
        )

        clear_program_compiled = compileTeal(
            self.nft_marketplace_asc1.clear_program(),
            mode=Mode.Application,
            version=self.teal_version
        )

        approval_program_bytes = NetworkInteraction.compile_program(
            client=self.client, source_code=approval_program_compiled
        )

        clear_program_bytes = NetworkInteraction.compile_program(
            client=self.client, source_code=clear_program_compiled
        )

        app_args = [
            decode_address(nft_owner_address),
            decode_address(self.creator_address),
        ]

        app_transaction = ApplicationTransactionRepository.create_application(
            client=self.client,
            creator_private_key=self.creator_pk,
            approval_program=approval_program_bytes,
            clear_program=clear_program_bytes,
            global_schema=self.nft_marketplace_asc1.global_schema,
            local_schema=self.nft_marketplace_asc1.local_schema,
            app_args=app_args,
            foreign_assets=[self.nft_id],
        )

        tx_id = NetworkInteraction.submit_transaction(
            self.client, transaction=app_transaction
        )

        transaction_response = self.client.pending_transaction_info(tx_id)

        self.app_id = transaction_response["application-index"]

        return tx_id

    def initialize_escrow(self):
        app_args = [
            self.nft_marketplace_asc1.AppMethods.initialize_escrow,
            decode_address(self.escrow_address),
        ]

        initialize_escrow_txn = ApplicationTransactionRepository.call_application(
            client=self.client,
            caller_private_key=self.creator_pk,
            app_id=self.app_id,
            on_complete=algo_txn.OnComplete.NoOpOC,
            app_args=app_args,
            foreign_assets=[self.nft_id],
        )

        tx_id = NetworkInteraction.submit_transaction(
            self.client, transaction=initialize_escrow_txn
        )

        return tx_id

    def fund_escrow(self):
        fund_escrow_txn = PaymentTransactionRepository.payment(
            client=self.client,
            sender_address=self.creator_address,
            receiver_address=self.escrow_address,
            amount=1000000,
            sender_private_key=self.creator_pk,
            sign_transaction=True,
        )

        tx_id = NetworkInteraction.submit_transaction(
            self.client, transaction=fund_escrow_txn
        )

        return tx_id

    def make_sell_offer(self, sell_price: int, nft_owner_pk):
        app_args = [self.nft_marketplace_asc1.AppMethods.make_sell_offer, sell_price]

        app_call_txn = ApplicationTransactionRepository.call_application(
            client=self.client,
            caller_private_key=nft_owner_pk,
            app_id=self.app_id,
            on_complete=algo_txn.OnComplete.NoOpOC,
            app_args=app_args,
            sign_transaction=True,
        )

        tx_id = NetworkInteraction.submit_transaction(self.client, transaction=app_call_txn)
        return tx_id

    def buy_nft(self,
                nft_owner_address, buyer_address, buyer_pk, buy_price):
        # 1. Application call txn
        app_args = [
            self.nft_marketplace_asc1.AppMethods.buy
        ]

        app_call_txn = ApplicationTransactionRepository.call_application(client=self.client,
                                                                         caller_private_key=buyer_pk,
                                                                         app_id=self.app_id,
                                                                         on_complete=algo_txn.OnComplete.NoOpOC,
                                                                         app_args=app_args,
                                                                         sign_transaction=False)

        # 2. Payment transaction: buyer -> seller
        asa_buy_payment_txn = PaymentTransactionRepository.payment(client=self.client,
                                                                   sender_address=buyer_address,
                                                                   receiver_address=nft_owner_address,
                                                                   amount=buy_price,
                                                                   sender_private_key=None,
                                                                   sign_transaction=False)

        # 3. Asset transfer transaction: escrow -> buyer

        asa_transfer_txn = ASATransactionRepository.asa_transfer(client=self.client,
                                                                 sender_address=self.escrow_address,
                                                                 receiver_address=buyer_address,
                                                                 amount=1,
                                                                 asa_id=self.nft_id,
                                                                 revocation_target=nft_owner_address,
                                                                 sender_private_key=None,
                                                                 sign_transaction=False)

        # Atomic transfer
        gid = algo_txn.calculate_group_id([app_call_txn,
                                           asa_buy_payment_txn,
                                           asa_transfer_txn])

        app_call_txn.group = gid
        asa_buy_payment_txn.group = gid
        asa_transfer_txn.group = gid

        app_call_txn_signed = app_call_txn.sign(buyer_pk)

        asa_buy_txn_signed = asa_buy_payment_txn.sign(buyer_pk)

        asa_transfer_txn_logic_signature = algo_txn.LogicSig(self.escrow_bytes)
        asa_transfer_txn_signed = algo_txn.LogicSigTransaction(asa_transfer_txn, asa_transfer_txn_logic_signature)

        signed_group = [app_call_txn_signed,
                        asa_buy_txn_signed,
                        asa_transfer_txn_signed]

        tx_id = self.client.send_transactions(signed_group)
        return tx_id
