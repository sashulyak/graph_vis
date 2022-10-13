# Visualization of users connections by their phone book contacts

To see visualization please visit https://sashulyak.github.io/graph_vis/
The graph is pretty big, so loading can take some time.

All the files in this repo except `create_graph.py` and `README.md` were generated automatically by Gephi and Sigma.js.

First, the source data was cleaned an converted into the GEXF graph.
Then visualized with the help of Gephi – https://gephi.org/ – open source graph visualization tool.
Gephi has a plugin called Sigma.js that allowed me to export the graph as an interactive HTML-page.

The source code of data preprocessing and graph generation is located in the file `create_graph.py`

## How to read the visualization

This graph shows connections between registered users and their phone book contacts.
- purple nodes (with people's names) – registered users
- yellow nodes (with title ???) – valuable unregistered persons. They occur in registered users' contact lists more than 10 times.
- gray nodes (with title ???) – unregistered users that occur in registered users' contact lists less than 10 times.

Edges are only between purple and other nodes. It was done for convenience to show how many unregistered users have friends that already use Ziina.
