import heapq
import bisect
import numpy as np
import random
from matplotlib import pyplot as plt
from CompanyAgent import CompanyAgent

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
        self.buyer_hist = []
        self.seller_hist = []
        self.sells = []
        self.buys = []
        self.trade_history = []

    def calculate_market_price(self, plot=False):
        #calc difference but only for the length of the shorter list
        shape = min(len(self.buys), len(self.sells))
        self.buys = np.sort(self.buys)[::-1]
        self.sells = np.sort(self.sells)
        difference = self.buys[:shape] - self.sells[:shape]
        intersection_idx = np.argwhere(difference <= 0)[0][0]
        intersection_price = (self.sells[intersection_idx] + self.buys[intersection_idx]) / 2
        self.market_price = intersection_price
        if plot:
            plt.plot(range(len(self.buys)), self.buys, label="Demand")
            plt.plot(range(len(self.sells)), self.sells, label="Supply")
            plt.axhline(intersection_price, color="black", linestyle="--", label="Market Price")
            plt.legend()
            plt.show()
            plt.hist(self.sells, bins=10, label="Sellers")
            plt.hist(self.buys, bins=10, label="Buyers")
            plt.axvline(self.market_price, color="black", linestyle="--", label="Market Price")
            plt.legend()
            plt.show()
    
    def get_trades_plot(self):
        #plot buyers and sellers
        plt.scatter(range(len(self.buyer_hist)), [agent.expected_market_price for agent in self.buyer_hist], label="Buyers")
        plt.scatter(range(len(self.seller_hist)), [agent.expected_market_price for agent in self.seller_hist], label="Sellers")
        plt.axhline(self.market_price, color="black", linestyle="--", label="Market Price")
        plt.legend()
        plt.show()

    def trade(self, buyer, seller):
        self.trade_history.append(buyer.expected_market_price)
        self.buyer_hist.append(buyer)
        self.seller_hist.append(seller)
        buyer.allowance += 1
        buyer.count -= 1
        seller.allowance -= 1
        seller.count -= 1

    def update(self):
        random.shuffle(self.agents)
        for agent in self.agents:
            # print(f"before {self.buyer_heap=}")
            # print(f"before {self.sellers=}")
            # print(f"before {self.best_buyer_price=}")
            # print(f"before {self.best_seller_price=}")
            # print(agent.state, agent.count, agent.expected_market_price, agent.expected_deficit)
            agent.update_agent()
            # print(agent.state, agent.count, agent.expected_market_price, agent.expected_deficit)
            if agent.state == "sell":
                self.sells += [agent.expected_market_price] * agent.count
                while agent.expected_market_price <= self.best_buyer_price:
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
                    if agent.expected_market_price < self.best_seller_price:
                        self.best_seller_price = agent.expected_market_price

            if agent.state == "buy":
                self.buys += [agent.expected_market_price] * agent.count
                if agent.expected_market_price >= self.best_seller_price:
                    #iterate over sellers and get first that is good enough
                    del_idx = []
                    for i, (_, seller) in enumerate(self.sellers):
                        price = seller.expected_market_price
                        if agent.expected_market_price < self.best_seller_price:
                            break
                        if price <= agent.expected_market_price:
                            #remove seller from list and trade
                            del_idx.append(i)
                            self.trade(agent, seller)
                            if seller.count == 0:
                                if seller.expected_market_price == self.best_seller_price:
                                    old_best_seller_price = self.best_seller_price
                                    self.best_seller_price = np.inf
                                    for _, seller in self.sellers:
                                        price = seller.expected_market_price
                                        if price < self.best_seller_price and price > old_best_seller_price:
                                            self.best_seller_price = price
                            
                            if agent.count == 0:
                                break
                    for i in reversed(del_idx):
                        del self.sellers[i]
                if agent.count > 0:
                    for c in range(agent.count):
                        heapq.heappush(self.buyer_heap, (-agent.expected_market_price, agent))         
                    if agent.expected_market_price > self.best_buyer_price:
                        self.best_buyer_price = agent.expected_market_price
            # print(f"after {self.buyer_heap=}")
            # print(f"after {self.sellers=}")
            # print(f"after {self.best_buyer_price=}")
            # print(f"after {self.best_seller_price=}")

        self.calculate_market_price(plot=True)
        self.get_trades_plot()
        self.sellers = []
        self.buyer_heap = []
        self.sells = []
        self.buys = []
        self.best_buyer_price = 0
        self.best_seller_price = np.inf
        self.counter = 0