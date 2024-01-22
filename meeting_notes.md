## Meeting with tutor 22-01-2024
- What to show during presentation? Trends in market depending on the initial parameters (abatement costs, num of buyers/sellers)?
- reducing allowance cap for market until producing is not more profitable? -> very cool
- could use whatever we want for initialization, Austria vs EU, init directly or sampling
- in presentation concentrate on big picture
- optimal trading strategies is an overkill but would be cool

## Status Update 20-01-2024

Our current model consists of agents with different price expectations, and allowance needs, that trade with each other—this way a market dynamic is created. The behaviour of the agents has a great influence on the behaviour of the market. To test different strategies, we now wondered how we should proceed, because of this feedback loop. Should we only use a subset of agents that deploy different strategies and measure the effectiveness of the agents (focus on the effectiveness of trading strategies for single agents) while the other agents stabilize the market, or should we change the general behaviour of all agents and then track how the market changes (focus on market behavior)? Or maybe something in between?

### Goal of the model/how can we play with the model:
- how hard can we cut CO2 before everything collapses?
- is our model close to the real data (price/co2 emission reduction/supply-demand)?
- market analysis: how companies react on co2 reduction measures? how many companies die/stop producing?
NaN	0.498065	30025304.0	2249863 - optimal trading strategies within market (Austria within Austria, Austria vs EU, EU vs EU)?
- concentrate on profit & allowances reduction? are the companies still making profit when the number of allowances goes down?


### Other questions:
- data to use for the market: (Austria within Austria, Austria vs EU, EU vs EU)?
- is okay to use data for init directly or should sample based on real data?
- what to concentrate on during the presentation?

### Need for initialization
- verified emissions - DONE
- allocation - DONE
- find companies which have the biggest % of the market
- how many % of emissions of the big companies are allocated for free - is there correlation with the size? are bigger companies compensated more than smaller and middle companies? are there differences in % of allocations depending on the company size? - DONE
- allowance cap from year to year in the whole market
- allocated % of the market cap
- average price per year
- difference between sectors over different countries - are some countries "greener" than others?
