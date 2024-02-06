import numpy as np
import random


class AllowanceOffer:
    def __init__(self, company_id, amount, price):
        self.company_id = company_id
        self.amount = amount
        self.price = price

    def __lt__(self, other):
        return self.price < other.price


class AllowanceBuy:
    def __init__(self, company_id, amount, price):
        self.company_id = company_id
        self.amount = amount
        self.price = price


class EmissionAllowanceAgent:
    def __init__(self,
                 id,
                 name,
                 allowance_balance,
                 x_prod, y_prod,
                 x_profit, y_profit,
                 lower_noise,
                 upper_noise,
                 allowance_points_per_production_volume):
        self.id = id
        self.name = name
        self.allowance_balance = allowance_balance
        self.consumed_allowance = 0
        self.days = 0
        self.profit = 0
        self.lower_noise = lower_noise  # [80, 100]
        self.upper_noise = upper_noise  # [100, 120]
        self.allowance_points_per_production_volume = allowance_points_per_production_volume
        self.production_function = np.polyfit(x_prod, y_prod, 3)
        self.profit_function = np.polyfit(x_profit, y_profit, 3)
        self.produced_volume = [-1] * 365
        self.provided_to_sell = 0

    def __repr__(self):
        return f"Id: {self.id} Profit: {self.profit} Remaining Allowance Points {self.allowance_balance}\n"

    def __str__(self):
        return f"Id: {self.id} Profit: {self.profit} Remaining Allowance Points {self.allowance_balance}\n"

    def production_volume_expected(self, day):
        result = 0.0
        for index, d in enumerate(self.production_function):
            result += d * day ** (len(self.production_function) - 1 - index)

        if result < 0:
            result = 0

        return result

    def expected_profit(self, production_volume):
        result = 0.0
        for index, d in enumerate(self.profit_function):
            result += d * production_volume ** (len(self.profit_function) - 1 - index)

        return result

    def allowance_points(self, production_volume):
        return production_volume * self.allowance_points_per_production_volume

    def expected_allowance_points_for_production(self):
        needed_points = 0.0
        for i in range(self.days, 365):
            needed_points += self.production_volume_expected(i)

        return self.allowance_points(needed_points)

    def perform_production_for_day(self, day):
        if self.produced_volume[day - 1] == -1:  # no production performed yet
            self.days = day
            expected_production = self.production_volume_expected(day) * random.randint(self.lower_noise,
                                                                                        self.upper_noise) / 100.0
            if self.allowance_balance >= self.allowance_points(expected_production):
                self.produced_volume[day - 1] = expected_production
                self.allowance_balance -= self.allowance_points(expected_production)
                self.consumed_allowance += self.allowance_points(expected_production)
                self.profit += self.expected_profit(expected_production) * self.produced_volume[day - 1]

    def overall_profit(self, day):
        return self.profit + self.allowance_balance / self.allowance_points_per_production_volume * self.profit(day)

    def price_for_sell(self, current_price, current_day):
        self.provided_to_sell = 0

        if self.expected_profit(self.production_volume_expected(current_day)) * 5 < current_price:
            self.provided_to_sell = self.allowance_balance
            return AllowanceOffer(self.id,
                                  self.provided_to_sell,
                                  current_price)

        elif self.expected_allowance_points_for_production() < self.allowance_balance:
            self.provided_to_sell = self.allowance_balance - self.expected_allowance_points_for_production()
            return AllowanceOffer(self.id,
                                  self.provided_to_sell,
                                  current_price * 1.2)

        else:
            return None


    def price_for_buy(self, current_price, current_day):
        if self.expected_allowance_points_for_production() > self.allowance_balance:
            return AllowanceBuy(self.id,
                                self.expected_allowance_points_for_production() - self.allowance_balance,
                                self.expected_profit(self.production_volume_expected(current_day))
                                if self.expected_profit(self.production_volume_expected(current_day)) >= 0
                                else 0)
        else:
            return None

    def change_allowance_balance(self, change_amount):
        self.allowance_balance += change_amount

    def change_profit_balance(self, change_amount):
        self.profit += change_amount


# ============================== SIMULATION ====================================================================
number_of_companies = 20
simulation_days = 365
market_price = 50
companies = []  # List of all companies in the simulation
total_allowance = 0
ids= []

offers = []  # For each day they can profit der offer, if they want to sell the allowance points

# =============================== INITIALISATION ===============================================================
for i in range(number_of_companies):
    allowance = random.randrange(1, 2)
    total_allowance += allowance
    companies.append(EmissionAllowanceAgent(i,
                                            "Company" + str(i),
                                            allowance,
                                            np.array([0.0, 90.0, 180.0, 270.0]),
                                            np.array([random.randrange(20, 80),
                                                      random.randrange(20, 80),
                                                      random.randrange(20, 80),
                                                      random.randrange(20, 80)]),
                                            np.array([0.0, 90.0, 180.0, 270.0]),
                                            np.array([random.randrange(20, 1000),
                                                      random.randrange(20, 1000),
                                                      random.randrange(20, 1000),
                                                      random.randrange(20, 1000)]),
                                            random.randrange(80, 100),
                                            random.randrange(100, 120),
                                            0.5))

# ============================== RUNNING MODEL =============================================================

for i in range(number_of_companies):
    ids.append(i)

for day in range(1, simulation_days):
    # Place the offers
    offers.clear()
    for company_id in range(number_of_companies):
        offer = companies[company_id].price_for_sell(market_price, day)
        if offer is not None:
            offers.append(offer)  # Get the offer of each company

    if len(offers) > 0:
        offers.sort()  # Sort the offers after the price

        # Perform the calculation of the market price
        market_price = 0
        for offer in offers:
            market_price += offer.price

        market_price /= len(offers)

        random.shuffle(ids)  # Change order because of who can get best price

        for company_id in ids:
            buy_offer = companies[company_id].price_for_buy(market_price, day)
            if buy_offer is not None:
                # Checking if offer is possible - get as much as possible
                for index, offer in enumerate(offers):
                    if offer.price < buy_offer.price:
                        if offer.amount > buy_offer.amount:
                            # 1. Case: Only use a part of the offer
                            trade_amount = buy_offer.amount
                            trade_costs = offer.price * trade_amount

                            # Add profit and reduce the points
                            companies[offer.company_id].change_profit_balance(trade_costs)
                            companies[offer.company_id].change_allowance_balance(-trade_amount)

                            # Reduce profit and add points
                            companies[buy_offer.company_id].change_profit_balance(-trade_costs)
                            companies[buy_offer.company_id].change_allowance_balance(trade_amount)

                            # Change the remaining offer - reduced by the amount
                            offers[index].amount -= trade_amount
                            buy_offer.amount -= trade_amount

                        else:
                            # 2. Case us the complete offer
                            trade_amount = offer.amount
                            trade_costs = offer.price * trade_amount

                            # Add profit and reduce the points
                            companies[offer.company_id].change_profit_balance(trade_costs)
                            companies[offer.company_id].change_allowance_balance(-trade_amount)

                            # Reduce profit and add points
                            companies[buy_offer.company_id].change_profit_balance(-trade_costs)
                            companies[buy_offer.company_id].change_allowance_balance(trade_amount)

                            # Change the remaining offer - reduced by the amount
                            offers.remove(offer)
                            buy_offer.amount -= trade_amount

    for company_id in range(number_of_companies):
        companies[company_id].perform_production_for_day(day)

print(companies)
remaining = 0
consumed = 0
for company in companies:
    remaining += company.allowance_balance
    consumed += company.consumed_allowance
print(total_allowance)
print(remaining)
print(consumed)
print(remaining+consumed)
