import math
import re

def parse_input_file(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()

    grid_info = lines[0].strip().split(',')
    N = int(grid_info[0])  
    M = int(grid_info[1]) 
    bend_penalty = int(grid_info[2]) 
    via_penalty = int(grid_info[3])  

    print(f"Parsed dimensions: N={N}, M={M}, Bend Penalty={bend_penalty}, Via Penalty={via_penalty}")

    obstacles = []
    nets = {}

    for line in lines[1:]:
        line = line.strip()
        if line.startswith("OBS"):
            parts = line.split('(')[1].rstrip(')').split(',')
            layer, x, y = map(int, parts)
            if 0 <= x < N and 0 <= y < M:
                obstacles.append((layer, x, y))
                # print(f"Valid obstacle added: Layer={layer}, x={x}, y={y}")
            # else:
                # print(f"Ignoring invalid obstacle: Layer={layer}, x={x}, y={y}")
        elif line.startswith("net"):
            net_name = line.split()[0]
            pins = []
            pin_matches = re.findall(r'\(\d+,\s*\d+,\s*\d+\)', line)
            for pin in pin_matches:
                layer, x, y = map(int, pin.strip("()").split(','))
                if 0 <= x < N and 0 <= y < M:
                    pins.append((layer, x, y))
                    # print(f"Valid pin added: Layer={layer}, x={x}, y={y}")
                # else:
                #     print(f"Ignoring invalid pin: Layer {layer}, ({x}, {y})")
            nets[net_name] = pins
            if not pins:
                print(f"Warning: Net '{net_name}' has no valid pins and will be skipped.")
                del nets[net_name]

    return N, M, bend_penalty, via_penalty, obstacles, nets

def initialize_grid(N, M):
    
    grid = {}
    for x in range(N):
        for y in range(M):
            grid[(x, y)] = {'cost': 1.0, 'obstacle': False}  # 
    return grid


def set_obstacles(grid_M0, grid_M1, obstacles):
 
    for layer, x, y in obstacles:
        if layer == 0:
            grid_M0[(x, y)]['cost'] = math.inf
            grid_M0[(x, y)]['obstacle'] = True
        elif layer == 1:
            grid_M1[(x, y)]['cost'] = math.inf
            grid_M1[(x, y)]['obstacle'] = True


def main():
    
    file_path = "input.txt"

   
    N, M, bend_penalty, via_penalty, obstacles, nets = parse_input_file(file_path)


    print(f"Grid Dimensions: {N}x{M}")
    print(f"Bend Penalty: {bend_penalty}, Via Penalty: {via_penalty}")
    print(f"Obstacles: {obstacles}")
    print(f"Nets: {nets}")


    grid_M0 = initialize_grid(N, M)
    grid_M1 = initialize_grid(N, M)

 
    set_obstacles(grid_M0, grid_M1, obstacles)


    print(f"M0[33, 44]: {grid_M0.get((33, 44), 'Not Found')}")
    print(f"M1[55, 77]: {grid_M1.get((55, 77), 'Not Found')}")


if __name__ == "_main_":
    main()