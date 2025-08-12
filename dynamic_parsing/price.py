def parse_event_price(price):
    if "-" in price:
        return None
    num = price.split("$")[1].split(" ")[0]
    try:
        num = float(num)
        if num == 0:
            return None
        return num
    except Exception as e:
        return None



if __name__ == "__main__":
    prices = ["From $21.41","$10-$20","From $0", "From $30 onwards"] # 21.41, None, None, 30
    for price in prices:
        print(parse_event_price(price))