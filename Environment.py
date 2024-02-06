import heapq
import numpy as np
import random
from matplotlib import pyplot as plt


class Environment:
    """The environment class for the carbon trading simulation, which models the market behavior.
    Properties:
        market_price (float): The current market price (intersection of supply and demand curves)
        agents (list): The list of agents
        daily_offers (list): A list of daily offers, used to calculate the supply curve
        daily_demands (list): A list of daily demands, used to calculate the demand curve
        trade_history_daily (list): A list of succesful daily trades
        market_price_history (list): A list of daily market prices
        trade_hist_dict (dict): A dictionary of trade history, containing the day, trade price, and trade amount
        market_hist_dict (dict): A dictionary of market price history, containing the day and market price
        agent_hist_dict (dict): A dictionary of agent history, containing the day, deficit, state, and trading volume of each agent
    """

    def __init__(self, initial_market_price, agents, mode):
        """Initializes the environment with the initial market price and the agents
        Args:
            initial_market_price (float): The initial market price
            agents (list): A list of agents
            mode (str): The mode of the environment. Can be "buyer_preferred" or "seller_preferred". 
                Buyer preferred means that the buyers are prioritized in the trade (random buyer chooses cheapest seller), 
                while seller preferred means that the sellers are prioritized in the trade (random seller chooses highest paying buyer).
        """
        self.market_price = initial_market_price
        self.agents = agents

        self.daily_offers = []
        self.daily_demands = []
        self.trade_history_daily = []
        self.market_price_history = []

        self.trade_hist_dict = {"day": [],
                                "trade_price": [], "trade_amount": []}
        self.market_hist_dict = {"day": [], "market_price": []}
        self.agent_hist_dict = {"day": [],
                                "deficit": [], "state": [], "count": []}

        if mode == "buyer_preferred":
            self.update = self.update_buyer_preferred
        elif mode == "seller_preferred":
            self.update = self.update_seller_preferred
        else:
            raise Exception("Mode not supported")

    def cartesian_product(self, *arrays):
        '''
        Returns the cartesian product of the input arrays.
        '''
        la = len(arrays)
        dtype = np.result_type(*arrays)
        arr = np.empty([len(a) for a in arrays] + [la], dtype=dtype)
        for i, a in enumerate(np.ix_(*arrays)):
            arr[..., i] = a
        return arr.reshape(-1, la)

    def calculate_market_price(self, plot=False):
        '''
        Calculates the market price based on the intersection between the supply and demand curves.
        Args:
            plot (bool): Whether to plot the supply and demand curves.'''

        demands = None
        if len(self.daily_demands) > 0 and len(self.daily_offers) > 0:
            # Sort demands in descending order. Each entry in demand is a tuple of (price, quantity).
            self.daily_demands = np.array(self.daily_demands)
            sort_idx = np.argsort(self.daily_demands[:, 0])[::-1]
            self.daily_demands[:, 0] = self.daily_demands[:, 0][sort_idx]
            self.daily_demands[:, 1] = self.daily_demands[:, 1][sort_idx]

            # Sort offers in ascending order
            self.daily_offers = np.array(self.daily_offers)
            sort_idx = np.argsort(self.daily_offers[:, 0])
            self.daily_offers[:, 0] = self.daily_offers[:, 0][sort_idx]
            self.daily_offers[:, 1] = self.daily_offers[:, 1][sort_idx]

            # Get the demand and supply curves by taking the cumulative sum of the quantities.
            demands = self.daily_demands
            demands[:, 1] = np.cumsum(demands[:, 1])
            offers = self.daily_offers
            offers[:, 1] = np.cumsum(offers[:, 1])

            # Calculate the intersection of the supply and demand curves.
            prices = self.cartesian_product(offers[:, 0], demands[:, 0])
            quantities = self.cartesian_product(offers[:, 1], demands[:, 1])
            potential_intersection_indices = np.argwhere(
                (prices[:, 0] <= prices[:, 1]) & (quantities[:, 0] < quantities[:, 1]))

            # update market price if an intersection is found, otherwise the old market price is kept.
            if len(potential_intersection_indices) > 0:
                intersection_idx = potential_intersection_indices[-1]
                intersection_price = (
                    prices[intersection_idx, 0] + prices[intersection_idx, 1]) / 2
                self.market_price = intersection_price[0]

        self.market_hist_dict["market_price"].append(self.market_price)
        self.market_hist_dict["day"].append(self.agents[0].day)

        if plot and demands is not None:
            self.get_supply_demand_plot(demands, offers)

    def get_supply_demand_plot(self, demands, offers):
        '''
        Plots the supply and demand curves and the efficient market price.
        '''
        plt.figure(figsize=(5, 3))
        plt.title(f"Supply and Demand Curves, Day: {self.agents[0].day}")
        plt.step(demands[:, 1], demands[:, 0], label="Demand")
        plt.step(offers[:, 1], offers[:, 0], label="Supply")
        plt.axhline(self.market_price, color="black",
                    linestyle="--", label="Market Price")
        plt.legend()
        plt.xlabel("Quantity")
        plt.ylabel("Price")
        plt.show()

    def trade(self, buyer, seller, trade_price):
        '''Trades between a buyer and a seller at the specified trade_price. 
        Updates the agents and saves the trade to the trade history.
        Args:
            buyer (Agent): The buyer
            seller (Agent): The seller
            trade_price (float): The price at which the trade occurs.
        '''
        trade_amount = min(buyer.count, seller.count)
        price = trade_price

        # update the agent allowances and selling/buying counts
        buyer.buy_allowance(trade_amount)
        seller.sell_allowance(trade_amount)

        self.trade_history_daily.append((price, trade_amount))
        self.trade_hist_dict["day"].append(self.agents[0].day)
        self.trade_hist_dict["trade_price"].append(price)
        self.trade_hist_dict["trade_amount"].append(trade_amount)

    def track_agent_state(self, agent):
        '''Tracks the state of the agent and saves it to the agent history.
        Args:
            agent (Agent): The agent to track.
        '''
        self.agent_hist_dict["day"].append(agent.day)
        self.agent_hist_dict["deficit"].append(agent.expected_deficit)
        self.agent_hist_dict["state"].append(agent.state)
        self.agent_hist_dict["count"].append(agent.count)

    def update_seller_preferred(self, plot=False):
        '''Updates the environment in seller preferred mode. 
        In this mode, the sellers are prioritized in the trade (random seller chooses highest paying buyer)
        The trade price is the highest price that the buyer is willing to pay, 
        and the trade occurs if the seller's price is lower than the buyer's price.
        Args:
            plot (bool): Whether to plot the supply and demand curves. Passed to calculate_market_price().'''

        buyer_heap = []  # adds buyers in descending order of trade price
        seller_list = []  # add selling agents

        # update internal agent state (based on emissions, allowances, prices, etc.) and add to the respective lists
        for agent in self.agents:
            self.track_agent_state(agent)
            agent.update_agent(self.market_price)
            if agent.state == "sell":
                self.daily_offers.append((agent.trade_price, agent.count))
                seller_list.append(agent)
            elif agent.state == "buy":
                self.daily_demands.append((agent.trade_price, agent.count))
                heapq.heappush(buyer_heap, (-agent.trade_price, agent))

        # shuffle the seller list to randomize the order of sellers
        random.shuffle(seller_list)

        # iterate through the sellers and assign best possible buyer.
        for seller in seller_list:
            buyer = None
            while len(buyer_heap) > 0 and seller.trade_price <= (-1)*buyer_heap[0][0] and seller.count > 0:
                trade_price, buyer = heapq.heappop(buyer_heap)
                self.trade(buyer, seller, trade_price=buyer.trade_price)

            # if seller still has allowances left => failed to sell, influences price expectations
            if seller.count > 0:
                seller.failed_sell()

            # if last checked buyer still has demand => re-add remaining volume to heap
            if buyer is not None and buyer.count > 0:
                heapq.heappush(buyer_heap, (-buyer.trade_price, buyer))

        # if there are still buyers left, they failed to buy, influences price expectations
        for buyer in buyer_heap:
            buyer[1].failed_buy()

        # update market price and reset daily offers and demands
        self.calculate_market_price(plot=plot)
        self.daily_offers = []
        self.daily_demands = []

    def update_buyer_preferred(self, plot=False):
        '''Updates the environment in buyer preferred mode. 
        In this mode, the buyers are prioritized in the trade (random buyer chooses cheapest seller).
        The trade price is the lowest price that the seller is willing to accept, 
        and the trade occurs if the buyer's price is higher than the seller's price.
        Args:
            plot (bool): Whether to plot the supply and demand curves. Passed to calculate_market_price().
        '''
        seller_heap = []  # adds sellers in ascending order of trade price
        buyer_list = []  # add buying agents

        # update internal agent state (based on emissions, allowances, prices, etc.) and add to the respective lists
        for agent in self.agents:
            self.track_agent_state(agent)
            agent.update_agent(self.market_price)
            if agent.state == "buy":
                self.daily_demands.append((agent.trade_price, agent.count))
                buyer_list.append(agent)
            elif agent.state == "sell":
                self.daily_offers.append((agent.trade_price, agent.count))
                heapq.heappush(seller_heap, (agent.trade_price, agent))

        # shuffle the buyer list to randomize the order of buyers
        random.shuffle(buyer_list)

        # iterate through the buyers and assign best possible seller.
        for buyer in buyer_list:
            seller = None
            while len(seller_heap) > 0 and buyer.trade_price >= seller_heap[0][0] and buyer.count > 0:
                trade_price, seller = heapq.heappop(seller_heap)
                self.trade(buyer, seller, trade_price=seller.trade_price)

            # if buyer still has demand => failed to buy, influences price expectations
            if buyer.count > 0:
                buyer.failed_buy()

            # if last checked seller still has allowances left => re-add remaining volume to heap
            if seller is not None and seller.count > 0:
                heapq.heappush(seller_heap, (seller.trade_price, seller))

        # if there are still sellers left, they failed to sell => influences price expectations
        for seller in seller_heap:
            seller[1].failed_sell()

        # update market price and reset daily offers and demands
        self.calculate_market_price(plot=plot)
        self.daily_offers = []
        self.daily_demands = []
