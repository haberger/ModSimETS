import numpy as np
import math

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

        self.min_sell_price = sell_price
        self.max_buy_price = buy_price  #max buying price, if higher it is not profitable to buy
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
    def update_expected_market_price(self):
        """
        Update the expected market price.
        """
        new_expected_market_price = (self.min_sell_price + self.max_buy_price) / 2 #TODO: ADD update rule
        if new_expected_market_price > self.max_buy_price:
            self.expected_market_price = self.max_buy_price
        elif new_expected_market_price < self.min_sell_price:
            self.expected_market_price = self.min_sell_price
        else:
            self.expected_market_price = new_expected_market_price

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