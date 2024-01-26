import numpy as np
import math

class CompanyAgent:
    def __init__(self, expected_emission, initial_allowance, min_sell_price, max_buy_price, expected_emission_noise=0.1, emission_rate_noise=0.01, activate_abatement=True, advanced_trading=False):
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

        self.emission_rate = (expected_emission + np.random.normal(scale=self.expected_emission_noise)) / 365.0   # Add some noise

        self.total_emission = 0
        self.day = 0
        self.expected_deficit = self.expected_emission - self.allowance

        self.expected_market_price = (min_sell_price+max_buy_price)/2
        
        self.sale_counter = 0
        self.buy_counter = 0
        self.count = 0
        self.state = "idle"
        self.trade_price = self.expected_market_price

        self.abatement_costs = self.init_abatement_costs()      #cost to reduce rate by 1 ton -> 
        if not activate_abatement:
            self.abatement_costs = [np.inf]
        self.abatement_cost_per_ton = self.abatement_costs[0] / 365.0

        self.min_sell_price = min_sell_price
        self.max_buy_price = max_buy_price
        if advanced_trading:
            self.update_market_position = self.update_market_position_advanced_training
        else:
            self.update_market_position = self.update_market_position_simple
        #self.max_buy_price = min(max_buy_price, self.abatement_cost_per_ton)#max buying price, if higher it is not profitable to buy
        

    def init_abatement_costs(self):
        abatement_costs = []
        start_value=np.random.gamma(shape=40, scale=700)
        variance_factor=np.random.uniform(0.5, 1.5)
        for variance in range(max(int(self.emission_rate*3), 1)):
            start_value += max(np.random.normal(scale=variance*variance_factor), 0)
            abatement_costs.append(start_value)
        return abatement_costs


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

    def update_abatements(self):
        """
        Update the abatements.
        """
        self.abatement_cost_per_ton = self.abatement_costs[0] / (366 - self.day) #first element is always the current abatement cost -> if taken pop
        #self.max_buy_price = min(self.max_buy_price, self.abatement_cost_per_ton)

    def update_expected_emission(self):
        """
        Update the expected emission for the year.
        """
        self.expected_emission = math.ceil((self.total_emission/self.day * 365)-1e-9) #TODO: maybe just look at past n days, might have more relevance
        self.expected_deficit = int(self.expected_emission - self.allowance)
        #print(self.expected_deficit)

    def update_market_position_simple(self):
        """
        post trade is necessary
        """

        if self.expected_deficit > 0:
            #buy or abate
            if self.expected_market_price > self.abatement_cost_per_ton:
                print("abate")
                self.state = "idle"
                self.count = 0
                self.abatement_costs.pop(0)
                self.emission_rate -= 1
            else:
                self.count = math.ceil(self.expected_deficit)
                self.state = "buy"
                self.trade_price = min(self.expected_market_price, self.max_buy_price)
        elif self.expected_deficit <= -1:
            #sell
            self.count = (-1)*math.ceil(self.expected_deficit)
            self.state = "sell"
            self.trade_price = max(self.expected_market_price, self.min_sell_price)
        else:
            self.state = "idle"
            self.count = 0

    def update_market_position_advanced_training(self):
        """
        post trade is necessary
        """

        if self.expected_deficit > 0:
            #buy or abate
            if self.expected_market_price > self.abatement_cost_per_ton:
                print("abate")
                self.state = "idle"
                self.count = 0
                self.abatement_costs.pop(0)
                self.emission_rate -= 1
            else:
                self.count = math.ceil(self.expected_deficit)
                self.state = "buy"
                self.trade_price = min(self.expected_market_price, self.max_buy_price)
        elif self.expected_deficit <= -30 or (self.day > 360 and self.expected_deficit < - 10):
            #sell
            self.count = (-1)*math.ceil(self.expected_deficit) - 10
            self.count = min(self.count, 10)
            self.state = "sell"
            self.trade_price = max(self.expected_market_price, self.min_sell_price)
        else:
            self.state = "idle"
            self.count = 0
    
    def sell_allowance(self, price, trade_amount):
        self.allowance -= trade_amount
        self.count -= trade_amount
        self.sale_counter += trade_amount


    def buy_allowance(self, price, trade_amount):
        self.allowance += trade_amount
        self.count -= trade_amount
        self.buy_counter += trade_amount
        

    def failed_sell(self):
        self.sale_counter -= self.count
    
    def failed_buy(self):
        self.buy_counter -= self.count

    def update_expected_market_price(self, market_price):
        
        if self.state == "sell":
            if self.sale_counter > 0: #successful sales
                self.expected_market_price += 1
            elif self.sale_counter < 0: #unsuccessful sales
                if self.expected_market_price > self.min_sell_price: #only reduce when min price was not used
                    self.expected_market_price -= 1

        elif self.state == "buy":
            if self.buy_counter > 0: #successful buys
                self.expected_market_price -= 1
            elif self.buy_counter < 0: #unsuccessful buys
                if self.expected_market_price < self.max_buy_price: #only increase when max price was not used
                    self.expected_market_price += 1
        elif self.state == 'idle' and self.day > 1:
            if self.expected_market_price > market_price:
                self.expected_market_price -= 1
            elif self.expected_market_price < market_price:
                self.expected_market_price += 1


        self.buy_counter = 0
        self.sale_counter = 0
        return

    def update_agent(self, market_price):
        """
        Update the agent.
        """
        self.day += 1
        self.update_expected_market_price(market_price)
        self.update_emission_rate()
        self.update_abatements()
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