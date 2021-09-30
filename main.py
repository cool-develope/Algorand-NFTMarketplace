from services.marketplace import NFTMarketplace


market = NFTMarketplace()

token1 = {
    "unit_name": "Photato",
    "asset_name": "authentium_nft_3",
    "description": "sell offer of vegetable",
    "url": "https://zsltrading.com/bd/wp-content/uploads/2017/07/Organic-Potato.jpg"
}


token2 = {
    "unit_name": "Garlic",
    "asset_name": "authentium_nft_4",
    "description": "sell offer of garlic",
    "url": "https://imagesvc.meredithcorp.io/v3/mm/image?url=https%3A%2F%2Fstatic.onecms.io%2Fwp-content%2Fuploads%2Fsites%2F24%2F2019%2F07%2Fgettyimages-513038872-2000.jpg&q=85"
}

token_id1 = market.register(1, token1)
token_id2 = market.register(2, token2)

market.sell_offer(1, token_id1, 1000000)

market.buy_offer(3, token_id1)