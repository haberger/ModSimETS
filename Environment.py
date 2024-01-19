import heapq
import bisect
import numpy as np
import random
from matplotlib import pyplot as plt
from CompanyAgent import CompanyAgent
import time

class Environment:

    def __init__(self, initial_market_price, agents):
        """
        Initialize the environment.

        Parameters:
        - initial_market_price (float): Initial price for allowances.
        """
        self.initial_market_price = initial_market_price
        self.market_price = self.initial_market_price
        self.agents = agents
        self.buyer_heap = [] # list of tuples (price, agent) sorted by price descending
        self.sellers = [] # list of tuples (price, agent) sorted by price ascending
        self.counter = 0
        self.best_buyer_price = 0
        self.best_seller_price = np.inf

        self.daily_buyers = []
        self.daily_sellers = []
        self.daily_trades = []

        self.sells = []
        self.buys = []
        self.trade_history = []

    def calculate_market_price(self, plot=False):
        #calc difference but only for the length of the shorter list
        shape = min(len(self.buys), len(self.sells))
        self.buys = np.sort(self.buys)[::-1]
        self.sells = np.sort(self.sells)
        if shape != 0:
            difference = self.buys[:shape] - self.sells[:shape]
            if sum(difference <= 0) > 0:
                intersection_idx = np.argwhere(difference <= 0)[0][0]
                intersection_price = (self.sells[intersection_idx] + self.buys[intersection_idx]) / 2
                self.market_price = intersection_price
        if plot:
            if True: #self.agents[0].day % 10 == 2:
                plt.figure()
                plt.plot(range(len(self.buys)), self.buys, label="Demand")
                plt.plot(range(len(self.sells)), self.sells, label="Supply")
                if shape != 0 and sum(difference <= 0) > 0:
                    plt.axhline(intersection_price, color="black", linestyle="--", label="Market Price")
                plt.legend()
                plt.show()
            #plt.savefig(f"fig/market_price{time.time()}.png")

            # plt.hist(self.sells, bins=10, label="Sellers")
            # plt.hist(self.buys, bins=10, label="Buyers")
            # plt.axvline(self.market_price, color="black", linestyle="--", label="Market Price")
            # plt.legend()
            # plt.show()
    
    def get_trades_plot(self):
        #plot buyers and sellers
        plt.scatter(range(len(self.daily_buyers)), [agent.trade_price for agent in self.daily_buyers], label="Buyers")
        plt.scatter(range(len(self.daily_sellers)), [agent.trade_price for agent in self.daily_sellers], label="Sellers")
        plt.axhline(self.market_price, color="black", linestyle="--", label="Market Price")
        plt.legend()
        plt.show()

    def trade(self, buyer, seller):
        price = buyer.trade_price
        self.trade_history.append(price)
        self.daily_buyers.append(buyer)
        self.daily_sellers.append(seller)
        self.daily_trades.append((buyer.trade_price, seller.trade_price))

        buyer.buy_allowance(price)
        seller.sell_allowance(price)
    
    def resolve_rest_market(self):

        for _, agent in self.sellers:
            agent.failed_sell()

        for _, agent in self.buyer_heap:
            agent.failed_buy()

        self.sellers = []
        self.buyer_heap = []


        self.daily_buyers = [] 
        self.daily_sellers = []
        self.daily_trades = []

        self.sells = []
        self.buys = []

        self.best_buyer_price = 0
        self.best_seller_price = np.inf
        self.counter = 0

    def update2(self):
            
        # seller heap
        sell_heap = []
        sell_list = []
        #buyer heap
        buy_heap = []
        buy_list = []

        #iterate over agents and add them to the heap
        for agent in self.agents:
            agent.update_agent()
            if agent.state == "sell":
                self.sells += [agent.trade_price] * agent.count
                for c in range(agent.count):
                    heapq.heappush(sell_heap, (agent.trade_price, agent))
                    sell_list.append(agent)
            elif agent.state == "buy":
                self.buys += [agent.trade_price] * agent.count
                for c in range(agent.count):
                    heapq.heappush(buy_heap, (-agent.trade_price, agent))
                    buy_list.append(agent)

        random.shuffle(sell_list)
        for seller in sell_list:
            if len(buy_heap) > 0 and seller.trade_price <= (-1)*buy_heap[0][0]:
                trade_price, buyer = heapq.heappop(buy_heap)
                self.trade(buyer, seller)
            else:
                seller.failed_sell()
            
        for buyer in buy_heap:
            buyer[1].failed_buy()

        self.calculate_market_price(plot=True)
        self.sellers = []
        self.buyer_heap = []


        self.daily_buyers = [] 
        self.daily_sellers = []
        self.daily_trades = []

        self.sells = []
        self.buys = []

        self.best_buyer_price = 0
        self.best_seller_price = np.inf
        self.counter = 0


    def update(self):
        random.shuffle(self.agents)
        for agent in self.agents:

            agent.update_agent()
            if agent.state == "sell":
                self.sells += [agent.trade_price] * agent.count
                while agent.trade_price <= self.best_buyer_price:
                    #pop best buyer from heap and trade
                    price, buyer = heapq.heappop(self.buyer_heap)
                    self.trade(buyer, agent)
                    if len(self.buyer_heap) > 0:
                        self.best_buyer_price = (-1)*self.buyer_heap[0][0]
                    else:
                        self.best_buyer_price = 0
                    if agent.count == 0:
                        break
                if agent.count > 0:
                    for c in range(agent.count):
                        bisect.insort(self.sellers,(self.counter, agent))
                        self.counter += 1
                    if agent.trade_price < self.best_seller_price:
                        self.best_seller_price = agent.trade_price

            if agent.state == "buy":
                self.buys += [agent.trade_price] * agent.count
                if agent.trade_price >= self.best_seller_price:
                    #iterate over sellers and get first that is good enough
                    del_idx = []
                    for i, (_, seller) in enumerate(self.sellers):
                        price = seller.trade_price
                        if agent.trade_price < self.best_seller_price:
                            break
                        if price <= agent.trade_price:
                            #remove seller from list and trade
                            del_idx.append(i)
                            self.trade(agent, seller)
                            if seller.count == 0:
                                if seller.trade_price == self.best_seller_price:
                                    old_best_seller_price = self.best_seller_price
                                    self.best_seller_price = np.inf
                                    for _, seller in self.sellers:
                                        price = seller.trade_price
                                        if price < self.best_seller_price and price > old_best_seller_price:
                                            self.best_seller_price = price
                            
                            if agent.count == 0:
                                break
                    for i in reversed(del_idx):
                        del self.sellers[i]
                if agent.count > 0:
                    for c in range(agent.count):
                        heapq.heappush(self.buyer_heap, (-agent.trade_price, agent))         
                    if agent.trade_price > self.best_buyer_price:
                        self.best_buyer_price = agent.trade_price
            # print(f"after {self.buyer_heap=}")
            # print(f"after {self.sellers=}")
            # print(f"after {self.best_buyer_price=}")
            # print(f"after {self.best_seller_price=}")

        self.calculate_market_price(plot=True)
        # self.get_trades_plot()

        self.resolve_rest_market()

