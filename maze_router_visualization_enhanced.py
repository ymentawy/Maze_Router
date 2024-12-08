import numpy as np
from queue import Queue
from typing import List, Tuple, Dict
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import colorsys
import matplotlib.colors as mcolors
import re
import os
import argparse

class LeeRouter:
   
    def _generate_unique_color(self):
        """
        Generate a unique color for a new net by cycling through HSV color space
        to ensure distinct colors from previously assigned colors
        """
       
        if not self.net_colors:
            return '#1E90FF'  

        
        existing_hues = [self._rgb_to_hue(mcolors.to_rgb(color)) for color in self.net_colors.values()]

       
        for attempt in range(100):  
            
            new_hue = np.random.random()

            
            if all(abs(new_hue - existing) > 0.2 for existing in existing_hues):
                
                rgb = colorsys.hsv_to_rgb(new_hue, 0.8, 0.8)
                new_color = mcolors.to_hex(rgb)
                return new_color

        
        fallback_colors = ['#1F77B4', '#FF7F0E', '#2CA02C', '#D62728', '#9467BD',
                           '#8C564B', '#E377C2', '#7F7F7F', '#BCBD22', '#17BECF']
        for color in fallback_colors:
            if color not in self.net_colors.values():
                return color

       
        return mcolors.to_hex(np.random.random(3))
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
        self.net_colors = {}  

  

    @classmethod
    def from_file(cls, file_path: str) -> "LeeRouter":
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Input file '{file_path}' not found!")

            with open(file_path, 'r') as file:
                lines = file.readlines()

            if len(lines) < 1:
                raise ValueError("Input file is empty or incorrectly formatted!")

            
            try:
                grid_info = lines[0].strip().split(',')
                N = int(grid_info[0])  
                M = int(grid_info[1]) 
                bend_penalty = int(grid_info[2]) 
                via_penalty = int(grid_info[3])
            except (IndexError, ValueError):
                raise ValueError("Error parsing grid dimensions or penalties from the input file.")

            
            router = cls(N, M, bend_penalty, via_penalty)

            
            for line in lines[1:]:
                line = line.strip()
                if line.startswith("OBS"):
                    try:
                        parts = line.split('(')[1].rstrip(')').split(',')
                        layer, x, y = map(int, parts)
                        router.add_obstacle(layer, x, y)
                    except (IndexError, ValueError):
                        print(f"Skipping invalid obstacle line: {line}")
                elif line.startswith("net"):
                    net_name = line.split()[0]
                    pins = []
                    pin_matches = re.findall(r'\(\d+,\s*\d+,\s*\d+\)', line)
                    for pin in pin_matches:
                        try:
                            layer, x, y = map(int, pin.strip("()").split(','))
                            pins.append((layer, x, y))
                        except ValueError:
                            print(f"Skipping invalid pin: {pin} in net {net_name}")
                    router.routed_nets[net_name] = (pins, 0.0)  

            return router
    
    



    def add_obstacle(self, layer: int, x: int, y: int):
        if 0 <= layer < 2 and 0 <= x < self.width and 0 <= y < self.height:
            self.layers[layer][y, x] = -1
            self.obstacles.append((layer, x, y))

    def route_all_nets(self):
        self.sort_nets_by_priority()

        longest_route = 0
        total_wire_length = 0
        total_vias = 0

        for net_name, (pins, _) in self.routed_nets.items():
            while len(pins) >= 2:
                try:
                    path, cost = self.route_net(net_name, pins)
                    self.routed_nets[net_name] = (path, cost)

                    wire_length = len(path) - 1
                    vias = sum(1 for i in range(len(path) - 1) if path[i][0] != path[i + 1][0])
                    total_wire_length += wire_length
                    total_vias += vias
                    longest_route = max(longest_route, wire_length)

                    print(f"{net_name} routed with cost: {cost:.2f}")
                    break  # Exit the while loop if routing is successful
                except ValueError as e:
                    print(f"Failed to route {net_name}: {e}")
                    if len(pins) > 2:
                        print(f"Removing first pin and retrying for net {net_name}")
                        first_pin = pins.pop(0)  # Remove the first pin and try again
                        try:
                            path, cost = self.route_net(net_name, pins)
                            self.routed_nets[net_name] = (path, cost)

                            wire_length = len(path) - 1
                            vias = sum(1 for i in range(len(path) - 1) if path[i][0] != path[i + 1][0])
                            total_wire_length += wire_length
                            total_vias += vias
                            longest_route = max(longest_route, wire_length)

                            print(f"{net_name} routed with cost: {cost:.2f}")
                            break  # Exit the while loop if routing is successful
                        except ValueError as e:
                            print(f"Failed to route {net_name} after removing first pin: {e}")
                            pins.insert(0, first_pin)  # Return the first pin back
                            print(f"Removing second pin and retrying for net {net_name}")
                            pins.pop(1)  # Remove the second pin and try again
                    else:
                        print(f"Removing last pin and retrying for net {net_name}")
                        pins.pop()  # Remove the last pin and try again
                    if len(pins) < 2:
                        print(f"Not enough pins to route net {net_name} after removing isolated pins.")
                        break  # Exit the while loop if fewer than two pins are left

        print("\nRouting Metrics:")
        print(f"Longest Route: {longest_route} segments")
        print(f"Total Wire Length: {total_wire_length} segments")
        print(f"Total Number of Vias: {total_vias}")

    def net_priority(self, net: Tuple[str, List[Tuple[int, int, int]]]) -> Tuple[int, float]:
        """
        Heuristic for prioritizing nets.
        - Nets with fewer pins are prioritized first.
        - For nets with the same number of pins, prioritize shorter Manhattan distance.
        """
        net_name, pins = net
        num_pins = len(pins)

        total_distance = 0
        for i in range(len(pins) - 1):
            _, x1, y1 = pins[i]
            _, x2, y2 = pins[i + 1]
            total_distance += abs(x1 - x2) + abs(y1 - y2)

        
        return (num_pins, total_distance)

    def sort_nets_by_priority(self):
        """
        Sort nets by heuristic priority before routing.
        """
        sorted_nets = sorted(
            self.routed_nets.items(),
            key=lambda item: self.net_priority((item[0], item[1][0]))  
        )
        self.routed_nets = dict(sorted_nets)

       
        print("\nSorted nets by priority:")
        for net_name, (pins, _) in self.routed_nets.items():
            print(f"  {net_name}: Pins={pins}, Priority={self.net_priority((net_name, pins))}")

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

        return full_path, total_cost

    def _lee_route(self, start_layer: int, start_x: int, start_y: int, end_layer: int, end_x: int, end_y: int) -> Tuple[List[Tuple[int, int, int]], float]:
        directions = [
            (1, 0, 0), (-1, 0, 0),  
            (0, 1, 0), (0, -1, 0),   
            (0, 0, 1), (0, 0, -1)   
        ]

        wave_grid = [np.full((self.height, self.width), np.inf) for _ in range(2)]
        wave_grid[start_layer][start_y, start_x] = 0

        queue = Queue()
        queue.put((start_layer, start_x, start_y))

        came_from = {}
        last_direction = {}

        while not queue.empty():
            curr_layer, curr_x, curr_y = queue.get()

            if (curr_layer, curr_x, curr_y) == (end_layer, end_x, end_y):
                break

            for dx, dy, dlayer in directions:
                new_layer = curr_layer + dlayer
                new_x, new_y = curr_x + dx, curr_y + dy

                if not (0 <= new_layer < 2 and 0 <= new_x < self.width and 0 <= new_y < self.height):
                    continue

                if self.layers[new_layer][new_y, new_x] == -1:
                    continue

                if curr_layer == 0 and dy != 0:  
                    continue
                if curr_layer == 1 and dx != 0:  
                    continue

                move_cost = 1
                current_direction = (dx, dy, dlayer)
                last_dir = last_direction.get((curr_layer, curr_x, curr_y))
                if last_dir and last_dir != current_direction:
                    move_cost += self.bend_penalty
                if curr_layer != new_layer:
                    move_cost += self.via_penalty - 1

                new_cost = wave_grid[curr_layer][curr_y, curr_x] + move_cost

                if new_cost < wave_grid[new_layer][new_y, new_x]:
                    wave_grid[new_layer][new_y, new_x] = new_cost
                    queue.put((new_layer, new_x, new_y))
                    came_from[(new_layer, new_x, new_y)] = (curr_layer, curr_x, curr_y)
                    last_direction[(new_layer, new_x, new_y)] = current_direction

        if np.isinf(wave_grid[end_layer][end_y, end_x]):
            raise ValueError(f"No valid path found from {(start_layer, start_x, start_y)} to {(end_layer, end_x, end_y)}")

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

        colors = {
            'background': '#F0F0F0',  
            'grid': '#E0E0E0',       
            'layers': {
                'M0': '#4169E1',      
                'M1': '#32CD32'      
            },
            'obstacles': '#8B0000',   
            'start_points': '#00FF00',
            'end_points': '#FF0000',  
            'via_points': '#800080'   
        }

        for net_name in self.routed_nets.keys():
            if net_name not in self.net_colors:
                self.net_colors[net_name] = self._generate_unique_color()

        fig, ax = plt.subplots(figsize=(14, 10))  
        fig.suptitle('Two-Layer Maze Router Visualization', fontsize=16, fontweight='bold')

        ax.set_xlim(0, self.width)
        ax.set_ylim(0, self.height)
        ax.set_xticks(np.arange(0, self.width + 1, 2))  
        ax.set_yticks(np.arange(0, self.height + 1, 2))  
        ax.grid(color=colors['grid'], linestyle='--', linewidth=0.5)
        ax.set_facecolor(colors['background'])

        # Draw obstacles
        for layer, x, y in self.obstacles:
            ax.add_patch(
                patches.Rectangle(
                    (x, y), 1, 1,
                    facecolor=colors['obstacles'],
                    alpha=0.7,
                    edgecolor='black',
                    hatch='///' if layer == 1 else '',
                )
            )

        layer_styles = {
            'M0': {'linestyle': '-', 'marker': 'o'},     
            'M1': {'linestyle': '--', 'marker': 's'}      
        }

        # Draw routed nets
        for net_name, (path, _) in self.routed_nets.items():
            path_color = self.net_colors[net_name]
            for j in range(len(path) - 1):
                layer1, x1, y1 = path[j]
                layer2, x2, y2 = path[j + 1]
                layer_name = 'M0' if layer1 == 0 else 'M1'
                style = layer_styles[layer_name]

                ax.plot([x1 + 0.5, x2 + 0.5], [y1 + 0.5, y2 + 0.5],
                        color=path_color,
                        linewidth=3,
                        linestyle=style['linestyle'],
                        marker=style['marker'],
                        markersize=8,
                        alpha=0.7
                )

                # Add via points if changing layers
                if layer1 != layer2:
                    via_point = patches.Circle(
                        (x1 + 0.5, y1 + 0.5), 0.3,
                        facecolor=colors['via_points'],
                        edgecolor='black',
                        alpha=0.7
                    )
                    ax.add_patch(via_point)

            if path:
                start_layer, start_x, start_y = path[0]
                end_layer, end_x, end_y = path[-1]

                start_point = patches.Circle(
                    (start_x + 0.5, start_y + 0.5), 0.4,
                    facecolor=colors['start_points'],
                    edgecolor='black',
                    alpha=0.9
                )
                ax.add_patch(start_point)
                ax.text(start_x + 0.5, start_y + 0.5, 'S',
                        color='black', fontweight='bold', fontsize=10, ha='center', va='center')

                end_point = patches.Circle(
                    (end_x + 0.5, end_y + 0.5), 0.4,
                    facecolor=colors['end_points'],
                    edgecolor='black',
                    alpha=0.9
                )
                ax.add_patch(end_point)
                ax.text(end_x + 0.5, end_y + 0.5, 'T',
                        color='black', fontweight='bold', fontsize=10, ha='center', va='center')

        # Create separate legends
        layer_explanation = [
            patches.Patch(color=colors['layers']['M0'], alpha=0.3, label='Metal Layer 0'),
            patches.Patch(color=colors['layers']['M1'], alpha=0.6, label='Metal Layer 1'),
            patches.Patch(color=colors['obstacles'], alpha=0.7, label='Routing Obstacles'),
            patches.Patch(color=colors['via_points'], alpha=0.7, label='Via Points'),
            patches.Patch(color=colors['start_points'], alpha=0.9, label='Start Points (S)'),
            patches.Patch(color=colors['end_points'], alpha=0.9, label='End Points (T)'),
        ]
        first_legend = ax.legend(handles=layer_explanation,
                                loc='upper right',
                                bbox_to_anchor=(1.2, 1),
                                title='Layer and Point Explanation')

        ax.add_artist(first_legend)

        net_path_explanation = [
            patches.Patch(color=self.net_colors[net_name], alpha=0.7, label=f'{net_name} Path')
            for net_name in self.routed_nets.keys()
        ]
        ax.legend(handles=net_path_explanation,
                loc='lower right',
                bbox_to_anchor=(1.13, 0),
                title='Net Path Colors')

        ax.set_xlabel('X Coordinate', fontweight='bold')
        ax.set_ylabel('Y Coordinate', fontweight='bold')

        plt.tight_layout()
        plt.subplots_adjust(left=0.05, right=0.85, top=0.95, bottom=0.05) 
        plt.savefig('visualization.png', bbox_inches='tight')  
        plt.show()


def main():
    
    input_file = input("Enter name of the input file: ")
    router = LeeRouter.from_file(input_file)

   
    router.route_all_nets()

    
    router.save_routing("routing_output.txt")

   
    router.visualize_routing()

if __name__ == "__main__":
    main()
