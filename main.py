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
    "url": "https://image.shutterstock.com/image-photo/garlic-cloves-bulb-vintage-wooden-260nw-552242461.jpg"
}

token_id1 = market.register(1, token1)
token_id2 = market.register(2, token2)

print("2 tokens created!")

market.sell_offer(1, token_id1, 1000000)

print("sell offer")

market.buy_offer(3, token_id1)

print("buy offer")