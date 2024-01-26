import heapq
import bisect
import numpy as np
import random
from matplotlib import pyplot as plt
from CompanyAgent import CompanyAgent
import time

class Environment:

    def __init__(self, initial_market_price, agents, mode):
        """
        Initialize the environment.

        Parameters:
        - initial_market_price (float): Initial price for allowances.
        """
        print("hisst")
        self.initial_market_price = initial_market_price
        self.market_price = self.initial_market_price
        self.agents = agents

        self.daily_offers = []
        self.daily_demands = []
        self.trade_history_daily = []
        self.market_price_history = []

        self.trade_hist_dict = {"day":[], "trade_price":[], "trade_amount":[]}
        self.market_hist_dict = {"day":[], "market_price":[]}
        self.agent_hist_dict = {"day":[], "deficit":[], "state":[], "count":[]}

        if mode == "buyer_preferred":
            self.update = self.update_buyer_preferred
        elif mode == "seller_preferred":
            self.update = self.update_seller_preferred
        else:
            raise Exception("Mode not supported")
    def cartesian_product(self, *arrays):
        la = len(arrays)
        dtype = np.result_type(*arrays)
        arr = np.empty([len(a) for a in arrays] + [la], dtype=dtype)
        for i, a in enumerate(np.ix_(*arrays)):
            arr[...,i] = a
        return arr.reshape(-1, la)

    def calculate_market_price(self, plot=False):
        demands = None
        if len(self.daily_demands) > 0 and len(self.daily_offers) > 0:
            # print(f"Demands: {self.daily_demands[:, 1]}, Offers: {self.daily_offers[:, 1]}")

            self.daily_demands = np.array(self.daily_demands)
            self.daily_offers = np.array(self.daily_offers)
            sort_idx = np.argsort(self.daily_demands[:, 0])[::-1]
            self.daily_demands[:, 0] = self.daily_demands[:, 0][sort_idx]
            self.daily_demands[:, 1] = self.daily_demands[:, 1][sort_idx]

            # self.daily_offers = np.sort(self.daily_offers, axis=0)
            sort_idx = np.argsort(self.daily_offers[:, 0])
            self.daily_offers[:, 0] = self.daily_offers[:, 0][sort_idx]
            self.daily_offers[:, 1] = self.daily_offers[:, 1][sort_idx]

            demands = self.daily_demands
            demands[:, 1] = np.cumsum(demands[:, 1])
            offers = self.daily_offers
            offers[:, 1] = np.cumsum(offers[:, 1])

            prices = self.cartesian_product(offers[:, 0], demands[:, 0])
            quantities = self.cartesian_product(offers[:, 1], demands[:, 1])
            potential_intersection_indices = np.argwhere((prices[:, 0] <= prices[:, 1]) & (quantities[:, 0] < quantities[:, 1]))
            if len(potential_intersection_indices) > 0:
                intersection_idx = potential_intersection_indices[-1]
                intersection_price = (prices[intersection_idx, 0] + prices[intersection_idx, 1]) / 2
                self.market_price = intersection_price[0]
        self.market_hist_dict["market_price"].append(self.market_price)
        self.market_hist_dict["day"].append(self.agents[0].day)
        if plot:
            if demands is not None: #self.agents[0].day % 10 == 2:
                print("hi")
                plt.figure()
                plt.step(demands[:, 1], demands[:, 0], label="Demand")
                plt.step(offers[:, 1], offers[:, 0], label="Supply")
                plt.axhline(self.market_price, color="black", linestyle="--", label="Market Price")
                plt.legend()
                plt.show()

    def get_trades_plot(self):
        #plot buyers and sellers
        plt.scatter(range(len(self.daily_buyers)), [agent.trade_price for agent in self.daily_buyers], label="Buyers")
        plt.scatter(range(len(self.daily_sellers)), [agent.trade_price for agent in self.daily_sellers], label="Sellers")
        plt.axhline(self.market_price, color="black", linestyle="--", label="Market Price")
        plt.legend()
        plt.show()

    def trade(self, buyer, seller, trade_price):
        if buyer.count == 0 or seller.count == 0:
            print(f"Buyer count: {buyer.count}, Seller count: {seller.count}")
            raise Exception("Cannot trade with empty count")
        trade_amount = min(buyer.count, seller.count)
        price = trade_price
        self.trade_history_daily.append((price, trade_amount)) # TODO UPD TRADE HISTORY DAILY STUFF

        buyer.buy_allowance(price, trade_amount)
        seller.sell_allowance(price, trade_amount)
        self.trade_hist_dict["day"].append(self.agents[0].day)
        self.trade_hist_dict["trade_price"].append(price)
        self.trade_hist_dict["trade_amount"].append(trade_amount)

    def track_agent_state(self,agent):
        self.agent_hist_dict["day"].append(agent.day)
        self.agent_hist_dict["deficit"].append(agent.expected_deficit)
        self.agent_hist_dict["state"].append(agent.state)
        self.agent_hist_dict["count"].append(agent.count)

    def update_seller_preferred(self, plot=False):
        buyer_heap = []
        seller_list = []    

        for agent in self.agents:
            self.track_agent_state(agent)
            agent.update_agent(self.market_price)
            if agent.state == "sell":
                # self.daily_offers += [agent.trade_price] * agent.count
                # for c in range(agent.count):
                #     seller_list.append(agent)
                self.daily_offers.append((agent.trade_price, agent.count))
                seller_list.append(agent)
            elif agent.state == "buy":
                # self.daily_demands += [agent.trade_price] * agent.count
                # for c in range(agent.count):
                #     heapq.heappush(buyer_heap, (-agent.trade_price, agent))    
                self.daily_demands.append((agent.trade_price, agent.count))
                heapq.heappush(buyer_heap, (-agent.trade_price, agent))

        random.shuffle(seller_list)
        for seller in seller_list:
            buyer = None
            # if len(buyer_heap) > 0 and seller.trade_price <= (-1)*buyer_heap[0][0] and seller.count > 0:
            while len(buyer_heap) > 0 and seller.trade_price <= (-1)*buyer_heap[0][0] and seller.count > 0:
                trade_price, buyer = heapq.heappop(buyer_heap)
                self.trade(buyer, seller, trade_price=buyer.trade_price)
            
            if seller.count > 0:
                seller.failed_sell()

            if buyer is not None and buyer.count > 0:
                heapq.heappush(buyer_heap, (-buyer.trade_price, buyer))
            
        for buyer in buyer_heap:
            buyer[1].failed_buy()

        self.calculate_market_price(plot=plot)
        self.daily_offers = []
        self.daily_demands = []

    def update_buyer_preferred(self, plot=False):    
        seller_heap = []
        buyer_list = []    

        for agent in self.agents:
            self.track_agent_state(agent)
            agent.update_agent(self.market_price)
            if agent.state == "buy":
                self.daily_demands.append((agent.trade_price, agent.count))
                buyer_list.append(agent)
            elif agent.state == "sell":
                self.daily_offers.append((agent.trade_price, agent.count))
                heapq.heappush(seller_heap, (agent.trade_price, agent))

        random.shuffle(buyer_list)
        for buyer in buyer_list:
            seller = None
            while len(seller_heap) > 0 and buyer.trade_price >= seller_heap[0][0] and buyer.count > 0:
                trade_price, seller = heapq.heappop(seller_heap)
                self.trade(buyer, seller, trade_price=seller.trade_price)
            
            if buyer.count > 0:
                buyer.failed_buy()

            if seller is not None and seller.count > 0:
                heapq.heappush(seller_heap, (seller.trade_price, seller))
            
        for seller in seller_heap:
            seller[1].failed_sell()

        self.calculate_market_price(plot=plot)

        self.daily_offers = []
        self.daily_demands = []
