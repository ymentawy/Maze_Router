# -*- coding: utf-8 -*-
"""Maze_Router_Visualization.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1HjiBZjxWJptD9jSQMjKEf29X0OF9YKa3
"""

import numpy as np
from queue import Queue
from typing import List, Tuple, Dict
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import colorsys
import matplotlib.colors as mcolors



class LeeRouter:
    def __init__(self, width: int, height: int, bend_penalty: int, via_penalty: int):
        self.width = width
        self.height = height
        self.bend_penalty = bend_penalty
        self.via_penalty = via_penalty
        self.layers = [
            np.zeros((height, width), dtype=int),
            np.zeros((height, width), dtype=int)
        ]
        self.routed_nets: Dict[str, Tuple[List[Tuple[int, int, int]], float]] = {}
        self.obstacles: List[Tuple[int, int, int]] = []
        self.net_colors = {}  # Store unique colors for each net

    def add_obstacle(self, layer: int, x: int, y: int):
        if 0 <= layer < 2 and 0 <= x < self.width and 0 <= y < self.height:
            self.layers[layer][y, x] = -1
            self.obstacles.append((layer, x, y))

    def route_net(self, net_name: str, pins: List[Tuple[int, int, int]]) -> Tuple[List[Tuple[int, int, int]], float]:
        if len(pins) < 2:
            raise ValueError("Net must have at least two pins")

        adjusted_pins = [(max(0, min(layer, 1)), max(0, min(x, self.width - 1)), max(0, min(y, self.height - 1)))
                         for layer, x, y in pins]

        full_path = []
        total_cost = 0

        for i in range(len(adjusted_pins) - 1):
            start_layer, start_x, start_y = adjusted_pins[i]
            end_layer, end_x, end_y = adjusted_pins[i + 1]

            path, cost = self._lee_route(start_layer, start_x, start_y, end_layer, end_x, end_y)
            if not full_path:
                full_path.extend(path)
            else:
                full_path.extend(path[1:])
            total_cost += cost

        self.routed_nets[net_name] = (full_path, total_cost)
        return full_path, total_cost

    def _lee_route(self, start_layer: int, start_x: int, start_y: int, end_layer: int, end_x: int, end_y: int) -> Tuple[List[Tuple[int, int, int]], float]:
        directions = [
            (1, 0, 0), (-1, 0, 0),  # X directions
            (0, 1, 0), (0, -1, 0),   # Y directions
            (0, 0, 1), (0, 0, -1)    # Layer directions
        ]

        wave_grid = [np.full((self.height, self.width), np.inf) for _ in range(2)]
        wave_grid[start_layer][start_y, start_x] = 0

        queue = Queue()
        queue.put((start_layer, start_x, start_y))

        came_from = {}
        last_direction = {}  # Track last movement direction to calculate bends

        while not queue.empty():
            curr_layer, curr_x, curr_y = queue.get()

            if (curr_layer, curr_x, curr_y) == (end_layer, end_x, end_y):
                break

            for dx, dy, dlayer in directions:
                new_layer = curr_layer + dlayer
                new_x, new_y = curr_x + dx, curr_y + dy

                # Check grid boundaries
                if not (0 <= new_layer < 2 and 0 <= new_x < self.width and 0 <= new_y < self.height):
                    continue

                # Check for obstacles
                if self.layers[new_layer][new_y, new_x] == -1:
                    continue

                # Layer-specific routing constraints
                if curr_layer == 0 and dy != 0:  # M0 is for horizontal
                    continue
                if curr_layer == 1 and dx != 0:  # M1 is for vertical
                    continue

                # Calculate move cost
                move_cost = 1

                # Calculate bend penalty
                current_direction = (dx, dy, dlayer)
                last_dir = last_direction.get((curr_layer, curr_x, curr_y))
                if last_dir and last_dir != current_direction:
                    move_cost += self.bend_penalty

                # Via penalty
                if curr_layer != new_layer:
                    move_cost += self.via_penalty - 1

                new_cost = wave_grid[curr_layer][curr_y, curr_x] + move_cost

                # Update if new path is cheaper
                if new_cost < wave_grid[new_layer][new_y, new_x]:
                    wave_grid[new_layer][new_y, new_x] = new_cost
                    queue.put((new_layer, new_x, new_y))
                    came_from[(new_layer, new_x, new_y)] = (curr_layer, curr_x, curr_y)
                    last_direction[(new_layer, new_x, new_y)] = current_direction

        # Check if path was found
        if np.isinf(wave_grid[end_layer][end_y, end_x]):
            raise ValueError(f"No valid path found from {(start_layer, start_x, start_y)} to {(end_layer, end_x, end_y)}")

        # Reconstruct path
        path = []
        curr_pos = (end_layer, end_x, end_y)
        while curr_pos != (start_layer, start_x, start_y):
            path.append(curr_pos)
            curr_pos = came_from[curr_pos]
        path.append((start_layer, start_x, start_y))

        return path[::-1], wave_grid[end_layer][end_y, end_x]

    def save_routing(self, output_file: str):
        with open(output_file, 'w') as f:
            for net_name, (path, cost) in self.routed_nets.items():
                path_str = ' '.join([f"({layer},{x},{y})" for layer, x, y in path])
                f.write(f"{net_name} Cost: {cost:.2f} Path: {path_str}\n")

    def _generate_unique_color(self):
        """
        Generate a unique color for a new net by cycling through HSV color space
        to ensure distinct colors from previously assigned colors
        """
        # If no nets have been assigned colors yet, start with a base color
        if not self.net_colors:
            return '#1E90FF'  # Default first color

        # Get existing hue values
        existing_hues = [self._rgb_to_hue(mcolors.to_rgb(color)) for color in self.net_colors.values()]

        # Try to find a hue that's sufficiently different from existing ones
        for attempt in range(100):  # Limit attempts to prevent infinite loop
            # Generate a random hue
            new_hue = np.random.random()

            # Check if this hue is sufficiently different from existing hues
            if all(abs(new_hue - existing) > 0.2 for existing in existing_hues):
                # Convert HSV to RGB, then to hex
                rgb = colorsys.hsv_to_rgb(new_hue, 0.8, 0.8)
                new_color = mcolors.to_hex(rgb)
                return new_color

        # Fallback: use a distinct color from matplotlib's color cycle
        fallback_colors = ['#1F77B4', '#FF7F0E', '#2CA02C', '#D62728', '#9467BD',
                           '#8C564B', '#E377C2', '#7F7F7F', '#BCBD22', '#17BECF']
        for color in fallback_colors:
            if color not in self.net_colors.values():
                return color

        # Last resort: generate a truly random color
        return mcolors.to_hex(np.random.random(3))

    def _rgb_to_hue(self, rgb):
        """Convert RGB to HSV hue value"""
        r, g, b = rgb
        mx = max(r, g, b)
        mn = min(r, g, b)
        df = mx - mn
        if mx == mn:
            h = 0
        elif mx == r:
            h = (60 * ((g-b)/df) + 360) % 360
        elif mx == g:
            h = (60 * ((b-r)/df) + 120) % 360
        elif mx == b:
            h = (60 * ((r-g)/df) + 240) % 360
        return h / 360.0

    def visualize_routing(self):
          """
          Create a comprehensive single-grid visualization of the routing with dynamic color generation
          """
          # Expanded color palette for visualization
          colors = {
              'background': '#F0F0F0',  # Light gray background
              'grid': '#E0E0E0',        # Lighter gray grid lines
              'layers': {
                  'M0': '#4169E1',      # Royal Blue for Metal Layer 0 (Horizontal)
                  'M1': '#32CD32'       # Lime Green for Metal Layer 1 (Vertical)
              },
              'obstacles': '#8B0000',   # Dark Red for obstacles
              'start_points': '#00FF00',# Bright Green for ALL start points
              'end_points': '#FF0000',  # Bright Red for ALL end points
              'via_points': '#800080'   # Purple for via points
          }

          # Dynamically generate colors for nets
          for net_name in self.routed_nets.keys():
              if net_name not in self.net_colors:
                  self.net_colors[net_name] = self._generate_unique_color()

          # Create figure with a smaller aspect ratio to avoid clipping
          fig, ax = plt.subplots(figsize=(14, 10))  # Adjusted figure size
          fig.suptitle('Two-Layer Maze Router Visualization', fontsize=16, fontweight='bold')

          # Grid and basic setup
          ax.set_xlim(0, self.width)
          ax.set_ylim(0, self.height)
          ax.set_xticks(np.arange(0, self.width+1, 2))  # Adjust step size for grid
          ax.set_yticks(np.arange(0, self.height+1, 2))  # Adjust step size for grid
          ax.grid(color=colors['grid'], linestyle='--', linewidth=0.5)
          ax.set_facecolor(colors['background'])

          # Visualization of obstacles
          for layer, x, y in self.obstacles:
              layer_name = 'M0' if layer == 0 else 'M1'
              ax.add_patch(
                  patches.Rectangle(
                      (x, y), 1, 1,
                      facecolor=colors['obstacles'],
                      alpha=0.7,
                      edgecolor='black',
                      hatch='///' if layer == 1 else '',
                      label=f'Obstacle on {layer_name}'
                  )
              )

          # Visualization styles for different layers
          layer_styles = {
              'M0': {'linestyle': '-', 'marker': 'o'},      # Solid line, circle marker for M0 (Horizontal)
              'M1': {'linestyle': '--', 'marker': 's'}      # Dashed line, square marker for M1 (Vertical)
          }

          # Visualize nets
          for net_name, (path, _) in self.routed_nets.items():
              # Use dynamically generated color for each net
              path_color = self.net_colors[net_name]

              # Plot each segment of the net
              for j in range(len(path) - 1):
                  layer1, x1, y1 = path[j]
                  layer2, x2, y2 = path[j+1]

                  # Determine layer name
                  layer_name = 'M0' if layer1 == 0 else 'M1'

                  # Get layer-specific style
                  style = layer_styles[layer_name]

                  # Draw path segments
                  ax.plot([x1+0.5, x2+0.5], [y1+0.5, y2+0.5],
                          color=path_color,
                          linewidth=3,
                          linestyle=style['linestyle'],
                          marker=style['marker'],
                          markersize=8,
                          label=f"{net_name} Path on {layer_name}",
                          alpha=0.7
                  )

                  # Highlight via points
                  if layer1 != layer2:
                      via_point = patches.Circle(
                          (x1+0.5, y1+0.5), 0.3,
                          facecolor=colors['via_points'],
                          edgecolor='black',
                          alpha=0.7,
                          label=f'Via Point between M0 and M1'
                      )
                      ax.add_patch(via_point)

              # Explicitly highlight start and end points
              if path:
                  # Start point
                  start_layer, start_x, start_y = path[0]
                  start_point = patches.Circle(
                      (start_x+0.5, start_y+0.5), 0.4,
                      facecolor=colors['start_points'],
                      edgecolor='black',
                      alpha=0.9
                  )
                  ax.add_patch(start_point)

                  # Add 'S' text to start point
                  ax.text(start_x+0.5, start_y+0.5, 'S',
                          color='black',
                          fontweight='bold',
                          fontsize=10,
                          ha='center',
                          va='center')

                  # End point
                  end_layer, end_x, end_y = path[-1]
                  end_point = patches.Circle(
                      (end_x+0.5, end_y+0.5), 0.4,
                      facecolor=colors['end_points'],
                      edgecolor='black',
                      alpha=0.9
                  )
                  ax.add_patch(end_point)

                  # Add 'T' text to end point
                  ax.text(end_x+0.5, end_y+0.5, 'T',
                          color='black',
                          fontweight='bold',
                          fontsize=10,
                          ha='center',
                          va='center')

          # Comprehensive Legends
          # Layer Types Legend
          layer_explanation = [
              patches.Patch(color=colors['layers']['M0'], alpha=0.3, label='Metal Layer 0 (Horizontal Routing)'),
              patches.Patch(color=colors['layers']['M1'], alpha=0.6, label='Metal Layer 1 (Vertical Routing)'),
              patches.Patch(color=colors['obstacles'], alpha=0.7, label='Routing Obstacles'),
              patches.Patch(color=colors['via_points'], alpha=0.7, label='Via Points (Inter-Layer Connections)'),
              patches.Patch(color=colors['start_points'], alpha=0.9, label='Start Points (S)'),
              patches.Patch(color=colors['end_points'], alpha=0.9, label='End Points (T)'),
          ]

          # Net-specific Path Legend
          net_path_explanation = [
              patches.Patch(color=self.net_colors[net_name], alpha=0.7, label=f'{net_name} Path')
              for net_name in self.routed_nets.keys()
          ]

          # Create multiple legends
          first_legend = ax.legend(handles=layer_explanation,
                                    loc='center left',
                                    bbox_to_anchor=(1, 0.7),
                                    title='Layer and Point Explanation')
          ax.add_artist(first_legend)

          ax.legend(handles=net_path_explanation,
                    loc='center left',
                    bbox_to_anchor=(1, 0.3),
                    title='Net Path Colors')

          # Labels and final touches
          ax.set_xlabel('X Coordinate', fontweight='bold')
          ax.set_ylabel('Y Coordinate', fontweight='bold')

          plt.tight_layout()
          plt.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.05)  # Adjust margins
          plt.savefig('visualization.png', bbox_inches='tight')  # Save with tight bounding box
          plt.show()

def net_priority(net: Tuple[str, List[Tuple[int, int, int]]]) -> Tuple[int, float]:
    net_name, pins = net
    num_pins = len(pins)

    total_distance = 0
    for i in range(len(pins) - 1):
        _, x1, y1 = pins[i]
        _, x2, y2 = pins[i + 1]
        total_distance += abs(x1 - x2) + abs(y1 - y2)

    return (-num_pins, total_distance)

def main():
    router = LeeRouter(14, 14, 0, 0)

    # Add obstacles (same as before)
    obstacles = [
        (0, 8, 1), (0, 8, 2), (0, 8, 3), (0, 8, 4), (0, 8, 5), (0, 8, 6),
        (0, 9, 1), (0, 9, 2), (0, 9, 3), (0, 9, 4), (0, 9, 5), (0, 9, 6),
        (0, 7, 6), (0, 6, 6), (0, 5, 6),
        (0, 7, 7), (0, 7, 8), (0, 7, 9), (0, 7, 10), (0, 7, 11),

        (1, 8, 1), (1, 8, 2), (1, 8, 3), (1, 8, 4), (1, 8, 5), (1, 8, 6),
        (1, 9, 1), (1, 9, 2), (1, 9, 3), (1, 9, 4), (1, 9, 5), (1, 9, 6),
        (1, 7, 6), (1, 6, 6), (1, 5, 6),
        (1, 7, 7), (1, 7, 8), (1, 7, 9), (1, 7, 10), (1, 7, 11)
    ]

    for layer, x, y in obstacles:
        router.add_obstacle(layer, x, y)

    nets = [
        ("net1", [(0, 5, 5), (0, 11, 3)]),
        ("net2", [(0, 5, 5), (0, 9, 10)])
    ]

    nets = sorted(nets, key=net_priority)

    for net_name, pins in nets:
        try:
            path, cost = router.route_net(net_name, pins)
            print(f"{net_name} routing cost: {cost:.2f}")
        except ValueError as e:
            print(f"Failed to route {net_name}: {e}")

    router.save_routing("routing_output.txt")

    # Visualize the routing
    router.visualize_routing()

if __name__ == "__main__":
    main()