# FoodLoop AI - Dispatch & Vehicle Routing Optimization

## 1. Problem Formulation: CVRPTW with Expiry Constraints

Surplus food redistribution presents a unique operational research challenge: unlike standard package delivery, cargo is perishable, arrives in stochastic batches, and is bound by strict biological safety time windows.

We formulate this as a **Capacitated Vehicle Routing Problem with Time Windows (CVRPTW)** and Priority Precedence:

### Decision Variables:
$$x_{ijk} \in \{0, 1\}$$
Equal to $1$ if vehicle $k$ traverses the edge from location $i$ to location $j$, and $0$ otherwise.

$$t_i \ge 0$$
Arrival time at location $i$.

$$l_i \ge 0$$
Cumulative cargo load (in kg) on vehicle when departing node $i$.

### Objective Function:
$$\min \sum_{k} \sum_{i} \sum_{j} c_{ij} x_{ijk} + \sum_{p \in \text{Pickups}} \lambda_p \cdot \max(0, t_p - \text{SafeExpiry}_p)$$

Where:
- $c_{ij}$: Travel distance/duration between node $i$ and node $j$
- $\lambda_p$: Priority penalty coefficient weighted by food perishability risk
- $\text{SafeExpiry}_p$: Maximum safe shelf-life computed by the thermodynamic spoilage model

### Constraints:
1. **Flow Conservation**: Every visited pickup and dropoff node has exactly one incoming and outgoing arc.
2. **Vehicle Capacity**: $l_i \le Q_k$ where $Q_k$ is vehicle $k$'s maximum rated payload.
3. **Time Windows**: $a_i \le t_i \le b_i$ for all visited locations.
4. **Precedence (Pickup before Dropoff)**: For any matching food pair $(p, d)$, $t_p + \text{service\_time} \le t_d$ and $\text{Vehicle}(p) = \text{Vehicle}(d)$.

---

## 2. Solver Implementation: Google OR-Tools

We utilize Google OR-Tools `pywrapcp.RoutingModel` configured with:
- **First Solution Strategy**: `PARALLEL_CHEAPEST_INSERTION`
- **Local Search Metaheuristic**: `GUIDED_LOCAL_SEARCH`
- **Disjunction Penalties**: Permitted stop drops with heavy penalty ($\$100,000$) to guarantee feasibility when driver capacity is constrained.

---

## 3. High-Performance Heuristic Fallback

To guarantee high availability during edge deployments or environments without compiled C++ OR-Tools native libraries, FoodLoop features a greedy heuristic optimizer with:
- **Earliest Expiry First (EEF)** priority queueing
- **Haversine Geo-Clustering** for multi-stop pick consolidation
- **Dynamic vehicle load balancing** preventing vehicle overloading
