# -*- coding: utf-8 -*-
"""maze_router.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1i9xBgZWnBvSWxjw0RPvHdtZb0bhoPFsr
"""

import numpy as np
from queue import Queue
from typing import List, Tuple, Dict
from parser import parse_input_file

class LeeRouter:
    def __init__(self, height: int, width: int, bend_penalty: int, via_penalty: int):
        self.width = width
        self.height = height
        self.bend_penalty = bend_penalty
        self.via_penalty = via_penalty
        self.layers = [
            np.zeros((height, width), dtype=int),
            np.zeros((height, width), dtype=int)
        ]
        self.routed_nets: Dict[str, Tuple[List[Tuple[int, int, int]], float]] = {}

    def add_obstacle(self, layer: int, x: int, y: int):
        if 0 <= layer < 2 and 0 <= x < self.width and 0 <= y < self.height:
            self.layers[layer][y, x] = -1

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
            (1, 0, 0), (-1, 0, 0),
            (0, 1, 0), (0, -1, 0),
            (0, 0, 1), (0, 0, -1)
        ]

        wave_grid = [np.full((self.height, self.width), np.inf) for _ in range(2)]
        wave_grid[start_layer][start_y, start_x] = 0

        queue = Queue()
        queue.put((start_layer, start_x, start_y))

        came_from = {}

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

                if curr_layer != new_layer:
                    move_cost += self.via_penalty - 1
                    if not (new_x == end_x or new_y == end_y) or new_layer != end_layer:
                      move_cost += self.bend_penalty

                new_cost = wave_grid[curr_layer][curr_y, curr_x] + move_cost
                if new_cost < wave_grid[new_layer][new_y, new_x]:
                    wave_grid[new_layer][new_y, new_x] = new_cost
                    queue.put((new_layer, new_x, new_y))
                    came_from[(new_layer, new_x, new_y)] = (curr_layer, curr_x, curr_y)

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


def main():
    while True:
        inputFileName = input("Enter the name of the file, or X to leave: ")
        if (inputFileName == "X" or inputFileName == "x"):
            break
        print("\n")
        N, M, bend_penalty, via_penalty, obstacles, nets = parse_input_file(inputFileName)
        router = LeeRouter(N, M, bend_penalty, via_penalty)
        for obstacle in obstacles:
            router.add_obstacle(obstacle[0], obstacle[1], obstacle[2])
        for netName, netPoints in nets.items():
            print("POTATOOO", netName, netPoints)
            router.route_net(netName, netPoints)
        outputFileName = input("Enter the name of file to save the output: ")
        print("\n")
        router.save_routing(outputFileName)








    # router = LeeRouter(14, 14, 0, 0)

    # router.add_obstacle(0, 8, 1)
    # router.add_obstacle(0, 8, 2)
    # router.add_obstacle(0, 8, 3)
    # router.add_obstacle(0, 8, 4)
    # router.add_obstacle(0, 8, 5)
    # router.add_obstacle(0, 8, 6)

    # router.add_obstacle(0, 9, 1)
    # router.add_obstacle(0, 9, 2)
    # router.add_obstacle(0, 9, 3)
    # router.add_obstacle(0, 9, 4)
    # router.add_obstacle(0, 9, 5)
    # router.add_obstacle(0, 9, 6)

    # router.add_obstacle(0, 7, 6)
    # router.add_obstacle(0, 6, 6)
    # router.add_obstacle(0, 5, 6)

    # router.add_obstacle(0, 7, 7)
    # router.add_obstacle(0, 7, 8)
    # router.add_obstacle(0, 7, 9)
    # router.add_obstacle(0, 7, 10)
    # router.add_obstacle(0, 7, 11)

    # router.add_obstacle(1, 8, 1)
    # router.add_obstacle(1, 8, 2)
    # router.add_obstacle(1, 8, 3)
    # router.add_obstacle(1, 8, 4)
    # router.add_obstacle(1, 8, 5)
    # router.add_obstacle(1, 8, 6)

    # router.add_obstacle(1, 9, 1)
    # router.add_obstacle(1, 9, 2)
    # router.add_obstacle(1, 9, 3)
    # router.add_obstacle(1, 9, 4)
    # router.add_obstacle(1, 9, 5)
    # router.add_obstacle(1, 9, 6)

    # router.add_obstacle(1, 7, 6)
    # router.add_obstacle(1, 6, 6)
    # router.add_obstacle(1, 5, 6)

    # router.add_obstacle(1, 7, 7)
    # router.add_obstacle(1, 7, 8)
    # router.add_obstacle(1, 7, 9)
    # router.add_obstacle(1, 7, 10)
    # router.add_obstacle(1, 7, 11)

    # path, cost = router.route_net("net1", [(0, 5, 5), (0, 11, 3)])
    # print(f"Net1 routing cost: {cost:.2f}")

    # path, cost = router.route_net("net2", [(0, 5, 5), (0, 9, 10)])
    # print(f"Net1 routing cost: {cost:.2f}")

    # router.save_routing("routing_output.txt")

if __name__ == "__main__":
    main()