import numpy as np
import math

k = 365

class CompanyAgent:
    """The Company Agent class represents a company agent in the Emission Trading System (ETS) market.
    Properties:
        expected_emission (float): The expected emission over the course of the year.
        allowance (float): The allowance for the year.
        emission_rate (float): The emission rate (emission per day).
        emission_rate_noise (float): The noise in the emission rate (emission per day). Sampled from a normal distribution.
        total_emission (float): The total emission produced by the company so far.
        day (int): The day of the year.
        expected_deficit (float): The expected deficit of the company (expected emissions - allowance).
        expected_market_price (float): The expected market price from the company's perspective.
        sale_counter (int): The number of successful sales.
        buy_counter (int): The number of successful buys.
        count (int): The number of allowances to buy or sell.
        state (str): The state of the company (buy, sell, or idle).
        trade_price (float): The price at which the company is willing to trade.
        abatement_costs (list): The abatement costs for the company (cost to permanently reduce emission rate by 1 ton per day).
        abatement_cost_per_ton (float): The abatement cost per ton. If this cost is less than the expected CO2 price, the company will abate.
        min_sell_price (float): The minimum price at which the company can sell the allowances.
        max_buy_price (float): The maximum price at which the company can buy the allowances.
        expected_emission_noise (float): Initial uncertainty in the expected emission.
    """
    def __init__(self, expected_emission, initial_allowance, min_sell_price, max_buy_price, expected_emission_noise=0.1, emission_rate_noise=0.01, activate_abatement=True, advanced_trading=False):
        """Initialize the Company Agent.
        Args:
            expected_emission (float): The expected emission over the course of the year.
            initial_allowance (float): The initial allowance for the year.
            min_sell_price (float): The minimum price at which the company can sell the allowances.
            max_buy_price (float): The maximum price at which the company can buy the allowances.
            expected_emission_noise (float): Initial uncertainty in the expected emission.
            emission_rate_noise (float): The noise in the emission rate (emission per day).
            activate_abatement (bool): Whether to activate abatement or not.
            advanced_trading (bool): Whether to use advanced trading strategies or not.
        """

        self.expected_emission = expected_emission + np.random.normal(scale=expected_emission_noise) 
        self.allowance = initial_allowance

        self.emission_rate = (self.expected_emission) / 365.0   # Add some noise
        self.emission_rate_noise = emission_rate_noise

        self.total_emission = 0
        self.day = 0
        self.expected_deficit = self.expected_emission - self.allowance

        self.expected_market_price = (min_sell_price+max_buy_price)/2
        
        self.sale_counter = 0
        self.buy_counter = 0
        self.count = 0
        self.state = "idle"
        self.trade_price = self.expected_market_price

        self.abatement_costs = self.init_abatement_costs()  # cost to permanently reduce rate by 1 ton 
        if not activate_abatement:
            self.abatement_costs = [np.inf]
        self.abatement_cost_per_ton = float(np.inf)

        self.min_sell_price = min_sell_price
        self.max_buy_price = max_buy_price

        if advanced_trading:
            self.update_market_position = self.update_market_position_advanced_training
        else:
            self.update_market_position = self.update_market_position_simple
    
        self.last_k_emissions = [] 

    def init_abatement_costs(self):
        '''
        Initialize the abatement costs for the company.
        The initial abatement cost is generated using a gamma distribution. 
        The following abatement costs are generated by adding a random normal noise to the previous abatement cost (which is clamped to 0).
        Taking only positive values makes sure that the abatement costs increase over the number of reductions.
        '''
        abatement_costs = []
        start_value=np.random.gamma(shape=2.5, scale=10000)
        variance_factor=np.random.uniform(0.1 , 100)
        for variance in range(365):
            start_value += max(np.random.normal(scale=variance*variance_factor) + np.random.uniform(0,1000), 0)
            abatement_costs.append(start_value)
        return abatement_costs

    def update_emission_rate(self):
        """
        Update the emission rate. Models the emission rate as a Wiener process.
        """
        self.emission_rate = max(0, self.emission_rate + np.random.normal(scale=self.emission_rate_noise))
        # 3 percent chance that the emission rate is reduced by 1
        # if np.random.uniform(0,1) < 0.02:
        #     self.emission_rate += np.random.normal(scale = self.emission_rate_noise*8) #TODO maybe add bigger impacts

    def track_emission(self):
        """
        Track the emissions produced by the company.
        """
        self.total_emission += self.emission_rate
        self.last_k_emissions.append(self.emission_rate)
        if len(self.last_k_emissions) > k:
            self.last_k_emissions.pop(0)

    def update_abatements(self):
        """
        Update the abatement costs per ton for the company. It is calculated over the remaining days of the year.
        """
        # The first element is always the current abatement cost -> if its taken, its popped
        self.abatement_cost_per_ton = self.abatement_costs[0] / (366 - self.day) 

    def update_expected_emission(self):
        """
        Update the expected emission for the company based on previous emissions.
        Emission of last 10 days and today have higher weight.
        """
        
        total_average = sum(self.last_k_emissions)/len(self.last_k_emissions)
        average_last_10 = sum(self.last_k_emissions[-min(10, len(self.last_k_emissions)):])/min(10, len(self.last_k_emissions))

        # higher weight for the last 10 days and the current emission rate
        self.expected_emission = ((total_average + average_last_10 + self.last_k_emissions[-1])/3)*(365)

        # handle potential float issues
        self.expected_emission = math.ceil((self.expected_emission - 1e-9))

        self.expected_deficit = int(self.expected_emission - self.allowance)

    def update_market_position_simple(self):
        """
        Update the market position of the company based on the expected deficit.

        If the expected deficit is positive, the company will either instantly buy the missing allowances
        or abate if cost is lower than the expected market price.
        If the expected deficit is negative, the company will instantly sell the surplus allowances.
        """

        if self.expected_deficit > 0:
            #buy or abate
            if self.expected_market_price > self.abatement_cost_per_ton:
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
        Update the market position of the company based on the expected deficit with advanced trading strategies.

        If the expected deficit is positive, the company will either instantly buy a fraction of the missing allowances
        to spread out the trades (less risk to get a bad market price) or abate if cost is lower than the expected market price.
        """

        if self.expected_deficit > 0:
            #buy or abate
            if self.expected_market_price > self.abatement_cost_per_ton:
                self.state = "idle"
                self.count = 0
                self.abatement_costs.pop(0)
                self.emission_rate -= 1
            else:
                self.count = math.ceil(self.expected_deficit)

                # Dont buy everything at once, closer to the end of the year => buy bigger fractions
                # "Time in the market beats timing the market" or something like that
                self.count = np.ceil(np.random.uniform(max(self.day/358, 1), 1) * self.count)
                self.state = "buy"
                self.trade_price = min(self.expected_market_price, self.max_buy_price)
        
        else:
            # keep percentage of expected emission as risk buffer, at the end of the year the buffer is reduced
            risk_buffer = self.expected_emission * 0.01 if self.day < 351 else self.expected_emission * (365-self.day)/1500

            if self.expected_deficit <= -risk_buffer:
                #sell
                self.count = (-1)*math.ceil(self.expected_deficit) - risk_buffer
                self.count = np.floor(np.np.random.uniform(max(self.day/358,1), 1) * self.count)
                self.state = "sell"
                self.trade_price = max(self.expected_market_price, self.min_sell_price)

            else:
                self.state = "idle"
                self.count = 0
    
    def sell_allowance(self, trade_amount):
        """
        reduces the allowance and update trade count by the traded amount
        """

        self.allowance -= trade_amount
        self.count -= trade_amount
        #track successful sale
        self.sale_counter += trade_amount


    def buy_allowance(self, trade_amount):
        """
        increases the allowance and update the trade count by the traded amount
        """
        self.allowance += trade_amount
        self.count -= trade_amount
        #track successful buy
        self.buy_counter += trade_amount
        

    def failed_sell(self):
        '''
        tracks failed sales
        '''
        self.sale_counter -= self.count
    
    def failed_buy(self):
        '''
        tracks failed buys
        '''
        self.buy_counter -= self.count

    def update_expected_market_price(self, market_price):
        """
        Update the expected market price based on the trades of the previous day.
        If the company had more successful than unsuccessful sales, the expected market price increases and vice versa.
        If the company had more successful than unsuccessful buys, the expected market price decreases and vice versa.
        """
        
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

        Update market price, emission rate, abatement costs per ton, past emissions, expected emission, and market position in that order.
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
        Comparison operator for the company agent.

        Randomly returns True or False so no company has a bias during sorting.
        """
        return np.random.choice([True, False])