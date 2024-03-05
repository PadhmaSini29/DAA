import streamlit as st
import mysql.connector
import networkx as nx
import matplotlib.pyplot as plt


class MultistageGraph:
    def __init__(self):  # Corrected initialization method signature
        self.stages = [['Router 1', 'Router 2', 'Router 3'],  # stage 1
                       ['Switch 1', 'Switch 2', 'Switch 3'],  # stage 2
                       ['Firewall 1', 'Firewall 2', 'Firewall 3', 'Firewall 4'],  # stage 3
                       ['Server 1', 'Server 2', 'Server 3']]  # stage 4
        self.edges = {
            'Router 1': {'Switch 1': 10, 'Switch 2': 12},  # Dictionary to store edges and their costs
            'Router 2': {'Switch 1': 8, 'Switch 3': 14},
            'Router 3': {'Switch 2': 9, 'Switch 3': 15},
            'Switch 1': {'Firewall 1': 8, 'Firewall 2': 10},
            'Switch 2': {'Firewall 1': 7, 'Firewall 2': 12},
            'Switch 3': {'Firewall 3': 11, 'Firewall 4': 9},
            'Firewall 1': {'Server 1': 9, 'Server 2': 11},
            'Firewall 2': {'Server 1': 13, 'Server 2': 10},
            'Firewall 3': {'Server 2': 8, 'Server 3': 9},
            'Firewall 4': {'Server 2': 11, 'Server 3': 10}
        }

        

    def find_min_path_cost(self, source, destination):
        # Initialize cost dictionary for storing the minimum cost to each node
        cost_dict = {node: float('inf') for node in self.get_nodes()}
        # Set the cost of the source node as 0
        cost_dict[source] = 0
        # allocate a empty dictionary to store the previous node
        prev_node_dict = {}

        # Traverse each stage in the multistage graph
        for stage in self.stages[1:]:
            for node in stage:
                # Compute the minimum cost from the previous stage to the current node
                min_cost = float('inf')
                min_prev_node = None
                for prev_node in self.stages[self.stages.index(stage) - 1]:
                    if prev_node in self.edges and node in self.edges[prev_node]:
                        cost = cost_dict[prev_node] + self.edges[prev_node][node]
                        if cost < min_cost:
                            min_cost = cost
                            min_prev_node = prev_node

                # Update the minimum cost for the current node and store the minimum previous node
                cost_dict[node] = min_cost
                prev_node_dict[node] = min_prev_node

        path = [destination]
        curr_node = destination
        while curr_node != source:
            curr_node = prev_node_dict[curr_node]
            path.append(curr_node)

        path.reverse()
        return cost_dict[destination], path

    def get_nodes(self):
        nodes = []
        for stage in self.stages:
            nodes.extend(stage)
        return nodes


# Database configuration
database = 'network_mst'
host = 'localhost'
user = 'root'
password = 'padhmasini'


def save_to_database(source, destination, min_cost, path):
    # Establish a connection to the MySQL database
    cnx = mysql.connector.connect(
        host=host,
        user=user,
        password=password,
        database=database
    )

    # Create a cursor object to execute SQL queries
    cursor = cnx.cursor()

    # Insert the values into the table
    insert_query = """
    INSERT INTO network_mst (source_node, destination_node, min_cost, path)
    VALUES (%s, %s, %s, %s)
    """
    data = (source, destination, min_cost, ' -> '.join(path))
    cursor.execute(insert_query, data)
    cnx.commit()

    # Close the cursor and the database connection
    cursor.close()
    cnx.close()


def plot_graph(graph, title):
    pos = nx.spring_layout(graph)
    plt.figure(figsize=(8, 6))
    nx.draw_networkx(graph, pos, with_labels=True, node_color='lightblue',
                     node_size=500, font_size=10, font_color='black',
                     edge_color='gray', width=1, arrows=True)
    edge_labels = nx.get_edge_attributes(graph, 'weight')
    nx.draw_networkx_edge_labels(graph, pos, edge_labels=edge_labels)
    plt.title(title)
    st.pyplot(plt)


def main():
    # Create the input elements
    source_node = st.text_input("Source Node")
    destination_node = st.text_input("Destination Node")
    find_button = st.button("Find Path")

    # Handle button click
    if find_button:
        # Create an instance of the MultistageGraph class
        network = MultistageGraph()

        try:
            # Find the minimum path cost and path from source to destination
            min_cost, path = network.find_min_path_cost(source_node, destination_node)

            # Print the initial graph
            st.write("Initial Graph:")
            initial_graph = nx.DiGraph()
            initial_graph.add_nodes_from(network.get_nodes())
            for node, neighbors in network.edges.items():
                for neighbor, cost in neighbors.items():
                    initial_graph.add_edge(node, neighbor, weight=cost)
            plot_graph(initial_graph, "Initial Graph")

            # Print the minimum path
            st.write("\nShortest Path:")
            st.write(' -> '.join(path))
            st.write(f"Minimum Path Cost: {min_cost}")

            # Create a graph of the critical path
            critical_path = nx.DiGraph()
            for i in range(len(path) - 1):
                critical_path.add_edge(path[i], path[i + 1], weight=network.edges[path[i]][path[i + 1]])

            # Plot the critical path graph
            plot_graph(critical_path, "Critical Path Graph")

            # Save the data to the MySQL database
            save_to_database(source_node, destination_node, min_cost, path)
            st.success("Data saved to the database.")
        except KeyError:
            st.error("Invalid source or destination node.")


if __name__ == "__main__":  
    main()
