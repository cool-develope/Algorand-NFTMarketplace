from typing import Dict, List

from utils.credentials import get_account_credentials, get_client
from services.nft_service import NFTService

class NFTMarketplace:
    def __init__(self):
        self.tokens: Dict[str, NFTService] = {}
        self.offers: Dict[int, int] = {}
        self.client = get_client()

    def register(self, account_id: int,  token_info: Dict):
        creator_pk, creator_address, _ = get_account_credentials(account_id)

        nft_service = NFTService(creator_address, creator_pk, self.client, token_info)
        
        nft_service.create_nft()
        nft_service.app_initialization(nft_owner_address=creator_address)
        nft_service.change_nft_credentials_txn()

        self.tokens[nft_service.app_id] = nft_service

        return nft_service.app_id

    def sell_offer(self, account_id: int, app_id: str, sell_price: int = 1000000):
        owner_pk, _, _ = get_account_credentials(account_id)

        nft_service = self.tokens[app_id]

        if nft_service.creator_pk != owner_pk:
            print("Only the owner can offer!")
            return

        
        nft_service.initialize_escrow()
        nft_service.fund_escrow()
        nft_service.make_sell_offer(sell_price=sell_price, nft_owner_pk=owner_pk)

        self.offers[app_id] = sell_price

    def buy_offer(self, account_id: int, app_id: str):
        buyer_pk, buyer_address, _ = get_account_credentials(account_id)

        nft_service = self.tokens[app_id]
        
        nft_service.opt_in(buyer_pk)

        nft_service.buy_nft(nft_owner_address=nft_service.creator_address, buyer_address=buyer_address, buyer_pk=buyer_pk, buy_price=self.offers[app_id])

        del self.offers[app_id]
