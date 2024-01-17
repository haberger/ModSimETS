import numpy as np
import matplotlib.pyplot as plt
import math
import random
import heapq
import bisect


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
        self.trade_history = []
        self.sells = []
        self.buys = []
    
    def get_trades(self):
        for agent in agents:
            type, price, count = agent.post_trade()
            for _ in range(count):
                if type == "buy":
                    self.buys.append((price, agent))
                elif type == "sell":
                    self.sells.append((price, agent))
        self.buys = sorted(self.buys, reverse=True)
        self.sells = sorted(self.sells)

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
    
    def trade(self, buyer, seller):
        self.trade_history.append(buyer.expected_market_price)
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
        self.sellers = []
        self.buyer_heap = []
        self.sells = []
        self.buys = []
        self.best_buyer_price = 0
        self.best_seller_price = np.inf
        self.counter = 0

class CompanyAgent:
    def __init__(self, expected_emission, initial_allowance, sell_price, buy_price, expected_emission_noise=0.1, emission_rate_noise=0.01):
        """
        Initialize a Company Agent.

        Parameters:
        - expected_emission (float): Expected emission for the year.
        - initial_allowance (float): Initial allowance for the agent.
        - sell_price (float): Price at which the agent is willing to sell allowances.
        - buy_price (float): Price at which the agent is willing to buy allowances.
        """
        self.expected_emission_noise = expected_emission_noise
        self.emission_rate_noise = emission_rate_noise

        self.initial_exepected_emission = expected_emission
        self.initial_allowance = initial_allowance

        self.expected_emission = self.initial_exepected_emission
        self.allowance = self.initial_allowance

        self.sell_price = sell_price
        self.buy_price = buy_price  #max buying price, if higher it is not profitable to buy
        self.emission_rate = expected_emission / 365.0 + np.random.normal(scale=self.expected_emission_noise)  # Add some noise

        self.total_emission = 0
        self.day = 1
        self.expected_deficit = self.expected_emission - self.allowance

        self.expected_market_price = (sell_price+buy_price)/2
        self.count = 0
        self.state = "idle"


    def update_emission_rate(self):
        """
        Update the emission rate in a stochastic way.
        """
        # Update the emission rate with some stochastic noise
        self.emission_rate = max(0, self.emission_rate + np.random.normal(scale=self.emission_rate_noise))

    def track_emission(self):
        """
        Track the emissions produced by the company.
        """
        self.total_emission += self.emission_rate

    def update_expected_emission(self):
        """
        Update the expected emission for the year.
        """
        self.expected_emission = self.total_emission/self.day * 365
        self.day += 1
        self.expected_deficit = self.expected_emission - self.allowance

    def update_market_position(self):
        """
        post trade is necessary
        """
        if self.expected_deficit > 0:
            #buy
            self.count = math.ceil(self.expected_deficit)
            self.state = "buy"
        elif self.expected_deficit < -1:
            #sell
            self.count = (-1)*math.ceil(self.expected_deficit)
            self.state = "sell"
        else:
            self.state = "idle"
            self.count = 0


    def update_agent(self):
        """
        Update the agent.
        """

        self.update_emission_rate()
        self.track_emission()
        self.update_expected_emission()
        self.update_market_position()

    def __lt__(self, other):
        """
        Compare two Company Agents.
        """
        # return randomly true or false
        return np.random.choice([True, False])

    def __str__(self):
        """
        String representation of the Company Agent.
        """
        return f"Company Agent - Initial Expected Emission: {self.initial_exepected_emission}, Initial Allowance: {self.initial_allowance}, " \
               f"Sell Price: {self.sell_price}, Buy Price: {self.buy_price}, Emission Rate: {self.emission_rate} " \
               f"Total Emission: {self.total_emission}, Expected Emission: {self.expected_emission}, Allowance: {self.allowance}"
    
    def get_sell_price(self):
        return self.sell_price
    
    def get_buy_price(self):
        return self.buy_price



if __name__ == "__main__":
    random.seed(42)
    # create two agents
    # define 100 agents with random expected emission, initial allowance, sell price and buy price
    agents = []
    for i in range(10000):
        expected_emission = np.random.uniform(0, 100)
        initial_allowance = np.random.uniform(0, 100)
        sell_price = np.random.uniform(0, 100)
        buy_price = np.random.uniform(0, 100)
        agents.append(CompanyAgent(expected_emission, initial_allowance, sell_price, buy_price))

    
    env = Environment(5, agents)
    env.update()
    env = Environment(5, agents)
    env.update()
    env = Environment(5, agents)
    env.update()
    #plot hist of trades
    plt.hist(env.trade_history, bins=10)
    plt.show()
    print("good_bye")

