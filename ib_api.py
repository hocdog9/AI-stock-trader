import threading
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from ibapi.order import Order
from ibapi.utils import iswrapper

class IBApi(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)
        self.nextOrderId = None
        self.buying_power = None
        self.positions = []
        self.positions_retrieved = threading.Event()  # To signal when positions are retrieved
        self.order_completion = threading.Event()  # To track order execution stat

    @iswrapper
    def nextValidId(self, orderId):
        self.nextOrderId = orderId
        print(f"Next Valid Order ID: {self.nextOrderId}")
        self.reqAccountSummary(9001, "All", "BuyingPower")  # Request the buying power
        self.reqPositions()  # Request all open positions

    @iswrapper
    def accountSummary(self, reqId, account, tag, value, currency):
        if tag == "BuyingPower":
            self.buying_power = float(value)
            # print(f"Buying Power for account {account} in {currency}: {value}")

    # @iswrapper
    # def accountSummaryEnd(self, reqId):
    #     # print(f"AccountSummaryEnd. ReqId: {reqId}")

    @iswrapper
    def position(self, account, contract, position, avgCost):
        if position > 0:  # Only add positions that have positive quantity
            self.positions.append((contract, position))
            # print(f"Position: {contract.symbol}, Quantity: {position}, Avg Cost: {avgCost}")

    @iswrapper
    def positionEnd(self):
        print("All positions retrieved")
        if not self.positions:
            print("No open positions found.")
        else:
            for contract, position in self.positions:
                print(f"Symbol: {contract.symbol}, Quantity: {position}")
        self.positions_retrieved.set()  # Signal that all positions are retrieved

    @iswrapper
    def orderStatus(self, orderId, status, filled, remaining, avgFillPrice, permId, parentId, lastFillPrice, clientId, whyHeld, mktCapPrice):
        print(f"Order {orderId} status: {status}")
        if status in ["Filled", "Cancelled"]:
            self.order_completion.set()  # Signal order execution completion

    def sell_all_positions(self):
        if len(self.positions) <= 0:
            print("No positions to sell.")
            return
        
        self.positions_retrieved.clear()
        self.reqPositions()

        if not self.positions_retrieved.wait(timeout=10):
            print("Timeout while retrieving positions.")
            return

        for contract, position in self.positions:
            if position <= 0:
                print(f"Skipping position with zero or negative quantity: {contract.symbol}")
                continue

            self.order_completion.clear()
            sell_order = Order()
            sell_order.action = "SELL"
            sell_order.orderType = "MKT"
            sell_order.totalQuantity = position
            sell_order.eTradeOnly = ''
            sell_order.firmQuoteOnly = ''

            self.placeOrder(self.nextOrderId, contract, sell_order)
            print(f"Placed SELL order for {contract.symbol}: {position} shares")
            self.nextOrderId += 1

            if not self.order_completion.wait(timeout=10):
                print(f"Timeout waiting for sell order of {contract.symbol}.")
                continue
        print("All positions processed.")

    def trade_security(self, ticker, order_size, action):
        # Create the contract for the security
        contract = Contract()
        contract.symbol = ticker
        contract.secType = "STK"
        contract.exchange = "SMART"
        contract.currency = "USD"

        # Create the order
        order = Order()
        order.action = action
        order.orderType = "MKT"  # Market Order
        order.totalQuantity = order_size
        order.eTradeOnly = ''
        order.firmQuoteOnly =''

        # Place the order
        self.placeOrder(self.nextOrderId, contract, order)
        print(f"Placed {action} order for {ticker}: {order_size} shares")
        self.nextOrderId += 1  # Increment the order ID for the next order
