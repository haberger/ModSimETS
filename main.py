import random
from Environment import Environment
from CompanyAgent import CompanyAgent
import numpy as np
import matplotlib.pyplot as plt

if __name__ == "__main__":
    random.seed(42)
    # create two agents
    # define 100 agents with random expected emission, initial allowance, sell price and buy price
    agents = []
    for i in range(100):
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