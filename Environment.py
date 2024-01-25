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
        self.initial_market_price = initial_market_price
        self.market_price = self.initial_market_price
        self.agents = agents

        self.daily_offers = []
        self.daily_demands = []
        self.trade_history_daily = []
        self.market_price_history = []

        self.trade_hist_dict = {"day":[], "trade_price":[]}
        self.market_hist_dict = {"day":[], "market_price":[]}


        if mode == "buyer_preferred":
            self.update = self.update_buyer_preferred
        elif mode == "seller_preferred":
            self.update = self.update_seller_preferred
        else:
            raise Exception("Mode not supported")

    def calculate_market_price(self, plot=False):
        #calc difference but only for the length of the shorter list
        shape = min(len(self.daily_demands), len(self.daily_offers))
        self.daily_demands = np.sort(self.daily_demands)[::-1]
        self.daily_offers = np.sort(self.daily_offers)
        if shape != 0:
            difference = self.daily_demands[:shape] - self.daily_offers[:shape]
            if sum(difference <= 0) > 0:
                intersection_idx = np.argwhere(difference <= 0)[0][0]
                intersection_price = (self.daily_offers[intersection_idx] + self.daily_demands[intersection_idx]) / 2
                self.market_price = intersection_price
                self.market_hist_dict["market_price"].append(intersection_price)
            else:
                self.market_hist_dict["market_price"].append(self.market_price)
        else:
            self.market_hist_dict["market_price"].append(self.market_price)
        self.market_hist_dict["day"].append(self.agents[0].day)
        if plot:
            if True: #self.agents[0].day % 10 == 2:
                plt.figure()
                plt.plot(range(len(self.daily_demands)), self.daily_demands, label="Demand")
                plt.plot(range(len(self.daily_offers)), self.daily_offers, label="Supply")
                if shape != 0 and sum(difference <= 0) > 0:
                    plt.axhline(intersection_price, color="black", linestyle="--", label="Market Price")
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
        trade_amount = min(buyer.count, seller.count)
        price = trade_price
        self.trade_history_daily.append((price, trade_amount)) # TODO UPD TRADE HISTORY DAILY STUFF

        buyer.buy_allowance(price, trade_amount)
        seller.sell_allowance(price, trade_amount)
        self.trade_hist_dict["day"].append(self.agents[0].day)
        self.trade_hist_dict["trade_price"].append(price)
        self.trade_hist_dict["trade_amount"].append(trade_amount)

    def update_seller_preferred(self, plot=False):
        buyer_heap = []
        seller_list = []    

        for agent in self.agents:
            agent.update_agent()
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
            # if len(buyer_heap) > 0 and seller.trade_price <= (-1)*buyer_heap[0][0] and seller.count > 0:
            while len(buyer_heap) > 0 and seller.trade_price <= (-1)*buyer_heap[0][0] and seller.count > 0:
                trade_price, buyer = heapq.heappop(buyer_heap)
                self.trade(buyer, seller, trade_price=buyer.trade_price)
            
            if seller.count > 0:
                seller.failed_sell()

            if buyer.count > 0:
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
            agent.update_agent()
            if agent.state == "buy":
                self.daily_demands += [agent.trade_price] * agent.count
                for c in range(agent.count):
                    buyer_list.append(agent)
            elif agent.state == "sell":
                self.daily_offers += [agent.trade_price] * agent.count
                for c in range(agent.count):
                    heapq.heappush(seller_heap, (agent.trade_price, agent))

        random.shuffle(buyer_list)
        for buyer in buyer_list:
            if len(seller_heap) > 0 and buyer.trade_price >= seller_heap[0][0]:
                trade_price, seller = heapq.heappop(seller_heap)
                self.trade(buyer, seller, trade_price=seller.trade_price)
            else:
                buyer.failed_buy()
            
        for seller in seller_heap:
            seller[1].failed_sell()

        self.calculate_market_price(plot=plot)

        self.daily_offers = []
        self.daily_demands = []
