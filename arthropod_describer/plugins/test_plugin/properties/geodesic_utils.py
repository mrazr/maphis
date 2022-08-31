import math
import queue
import time
from pathlib import Path

import cv2
import numba
import numpy as np
from typing import List, Tuple
import typing

import skimage
from skimage import io
from skimage.morphology import skeletonize
from skimage.measure import regionprops_table
from scipy.ndimage import binary_fill_holes
import networkx


golay_e: List[np.ndarray] = [
    np.array([
        [0,  0,  0],
        [0,  1,  0],
        [0,  0,  0]
    ], dtype=np.int8),

    np.array([
        [0,  0,  0],
        [0,  1,  0],
        [0,  1,  0]
    ], dtype=np.int8),

    np.array([
        [0, 0, 0],
        [0, 1, 0],
        [0, 0, 1]
    ], dtype=np.int8),

    np.array([
        [0, 0, 0],
        [0, 1, 0],
        [0, 1, 1]
    ], dtype=np.int8)
]
for i in range(1, 4):
    for j in range(1, 4):
        golay_e.append(np.rot90(golay_e[i], k=j))

idx = len(golay_e)

golay_e.append(
    np.array([
        [0, 0,  0],
        [0, 1,  1],
        [0, 0,  1]
    ]),
)

for i in range(1, 4):
    golay_e.append(np.rot90(golay_e[idx], k=i))

e_codes: typing.Set[int] = set()
for e_letter in golay_e:
    code = 0
    i = 0
    for r in range(3):
        for c in range(3):
            code += abs(e_letter[r, c]) * 2**i
            i += 1
    e_codes.add(code)

@numba.jit
def encode_bin_img(bin_img: np.ndarray) -> np.ndarray:
    # bin_img_ = bin_img # np.pad(bin_img, pad_width=((1, 1), (1, 1)), constant_values=(0, 0))
    bin_img_ = np.zeros((bin_img.shape[0] + 2, bin_img.shape[1] + 2), dtype=bin_img.dtype)
    bin_img_[1:-1, 1:-1] = bin_img
    result = np.zeros_like(bin_img_, dtype=np.uint16)
    for r in range(1, bin_img_.shape[0] - 1):
        for c in range(1, bin_img_.shape[1] - 1):
            x = 0
            code = 0
            for i in range(-1, 2):
                for j in range(-1, 2):
                    code += bin_img_[r + i, c + j] * 2**x
                    x += 1
            result[r, c] = code
    return result[1:-1, 1:-1]


def find_e(encoded_bin_img: np.ndarray, e_letter_code: int) -> np.ndarray:
    return encoded_bin_img == e_letter_code


def find_skeleton_endpoints(skeleton: np.ndarray, e_letter_codes: List[int]) -> List[typing.Tuple[int, int]]:
    encoded = encode_bin_img(skeleton)
    endpoints = np.zeros_like(skeleton, dtype=np.bool)
    for e_letter_code in e_letter_codes:
        endpoints = np.logical_or(endpoints, encoded == e_letter_code)

    return np.argwhere(endpoints > 0)[:, ::-1]


def geodesic_distance_for_skeleton(sk: np.ndarray, src: typing.Tuple[int, int]) -> np.ndarray:
    pixels = np.argwhere(sk > 0)[:, ::-1]
    q = queue.PriorityQueue()
    unvisited: typing.Set[typing.Tuple[int, int]] = set()

    dst_f = 99999999 * np.ones_like(sk, dtype=np.float32)

    for pixel in pixels:
        priority = 99999999
        if pixel[0] == src[0] and pixel[1] == src[1]:
            priority = 0
            dst_f[pixel[1], pixel[0]] = 0
        node = (int(pixel[0]), int(pixel[1]))
        q.put((priority, node))
        unvisited.add(node)

    while not q.empty():
        node_dst, node = q.get()
        if node not in unvisited:
            continue
        dst_f[node[1], node[0]] = node_dst
        unvisited.remove(node)

        neighs = neighbors(node)

        for neigh in neighs:
            if neigh not in unvisited:
                continue
            dst = math.sqrt((neigh[0] - node[0]) * (neigh[0] - node[0]) +
                            (neigh[1] - node[1]) * (neigh[1] - node[1]))
            if (upd_dst := dst_f[node[1], node[0]] + dst) < dst_f[neigh[1], neigh[0]]:
                dst_f[neigh[1], neigh[0]] = upd_dst
                q.put((upd_dst, neigh))

    dst_f = np.where(dst_f >= 99999, -1, dst_f)

    return dst_f


def find_shortest_path(bin_img: np.ndarray, src: Tuple[int, int], dst: Tuple[int, int]) -> List[Tuple[int, int]]:
    pixels = np.argwhere(bin_img > 0)[:, ::-1]
    q = queue.PriorityQueue()
    unvisited: typing.Set[typing.Tuple[int, int]] = set()

    dst_f = 99999999 * np.ones_like(bin_img, dtype=np.float32)

    for pixel in pixels:
        priority = 99999999
        if pixel[0] == src[0] and pixel[1] == src[1]:
            priority = 0
            dst_f[pixel[1], pixel[0]] = 0
        node = (int(pixel[0]), int(pixel[1]))
        q.put((priority, node))
        unvisited.add(node)

    parents: typing.Dict[Tuple[int, int], Tuple[int, int]] = {src: src}

    while not q.empty():
        node_dst, node = q.get()
        if node not in unvisited:
            continue
        dst_f[node[1], node[0]] = node_dst
        unvisited.remove(node)

        if node == dst:
            break

        neighs = neighbors(node)

        for neigh in neighs:
            if neigh not in unvisited:
                continue
            dist = math.sqrt((neigh[0] - node[0]) * (neigh[0] - node[0]) +
                            (neigh[1] - node[1]) * (neigh[1] - node[1]))
            if (upd_dst := dst_f[node[1], node[0]] + dist) < dst_f[neigh[1], neigh[0]]:
                dst_f[neigh[1], neigh[0]] = upd_dst
                q.put((upd_dst, neigh))
                parents[neigh] = node

    # dst_f = np.where(dst_f >= 99999, -1, dst_f)

    px_path: List[Tuple[int, int]] = []

    curr_px = dst

    while curr_px != src:
        px_path.append(curr_px)
        curr_px = parents[curr_px]
    px_path.append(src)

    return px_path


def get_graph(bin_region: np.ndarray) -> networkx.Graph:
    start = time.time()
    yy, xx = np.nonzero(bin_region)

    G = networkx.Graph()
    start2 = time.time()
    for py, px in zip(yy, xx):
        G.add_node((px, py))
    print(f'adding nodes took {time.time() - start2} secs')
    start3 = time.time()
    for py, px in zip(yy, xx):
        for i in [-1, 0, 1]:
            for j in [-1, 0, 1]:
                if i == 0 and j == 0:
                    continue
                if (px + j, py + i) not in G:
                    continue
                if abs(i) + abs(j) == 2:
                    G.add_edge((px, py), (px + j, py + i), weight=1.41)
                else:
                    G.add_edge((px, py), (px + j, py + i), weight=1)
    print(f'adding edges took {time.time() - start3} secs')
    print(f'graph generation took {time.time() - start} secs')
    return G


def get_graph2(bin_region: np.ndarray) -> networkx.Graph:
    start = time.time()

    G = networkx.Graph()

    nodes, edges = generate_nodes_edges(bin_region)
    G.add_nodes_from(nodes)
    G.add_edges_from(edges)

    print(f'graph generation took {time.time() - start} secs')
    return G


@numba.njit
def generate_nodes_edges(bin_region: np.ndarray):
    yy, xx = np.nonzero(bin_region)

    nodes = set()
    edges = set()

    for i in range(len(yy)):
        nodes.add((xx[i], yy[i]))

    for k in range(len(yy)):
        px, py = xx[k], yy[k]
        for i in [-1, 0, 1]:
            for j in [-1, 0, 1]:
                if i == 0 and j == 0:
                    continue
                if (px + j, py + i) not in nodes:
                    continue
                if abs(i) + abs(j) == 2:
                    edges.add(((px, py), (px + j, py + i), {'weight': 1.41}))
                else:
                    edges.add(((px, py), (px + j, py + i), {'weight': 1.0}))

    return nodes, edges


def neighbors(p: typing.Tuple[int, int]) -> typing.Set[typing.Tuple[int, int]]:
    neighs = set()
    for i in range(-1, 2):
        for j in range(-1, 2):
            if i == 0 and j == 0:
                continue
            neighs.add((p[0] + j, p[1] + i))
    return neighs


def get_longest_geodesic(lab_img: np.ndarray, label: int) -> Tuple[List[Tuple[int, int]], float]:
    region = lab_img == label
    region = binary_fill_holes(region)

    rr, cc = np.nonzero(region > 0)
    if len(rr) == 0:
        return [], None
    top, left = int(np.min(rr)), int(np.min(cc))
    bottom, right = np.max(rr), np.max(cc)

    # get only the region of interest
    region_ = region[top - 1:bottom + 1, left - 1:right + 1]

    skeleton = skeletonize(region_)

    # find skeleton endpoints with HMT
    endpoint_pixels = find_skeleton_endpoints(skeleton, list(e_codes))
    endpoint_pixels = [(int(endp[0]), int(endp[1])) for endp in endpoint_pixels]

    geod_dists: List[np.ndarray] = []
    prop_function = np.zeros_like(skeleton, dtype=np.float32)

    # for every skeleton endpoint compute geodesic distance transform inside the skeleton
    for i, endpoint in enumerate(endpoint_pixels):
        dist = geodesic_distance_for_skeleton(skeleton, endpoint)
        geod_dists.append(dist)
        # update the propagation function
        prop_function = np.maximum(prop_function, dist)
        # io.imsave(f'/home/radoslav/geo_dist{i}.tiff', dist, check_contrast=False)
    # io.imsave('/home/radoslav/prop_func.tiff', prop_function, check_contrast=False)

    # find the maximum of the propagation function
    max_of_prop = np.max(prop_function)

    # ideally, find at least 2 endpoints that whose furthest pixel is at distance `max_of_prop`. Wont work now on circle-like regions
    extremes = np.argwhere(np.abs(prop_function - max_of_prop) < 1e-6)[:, ::-1]

    if extremes.shape[0] < 2 or len(endpoint_pixels) < 2:
        lab = skimage.measure.label(region, connectivity=2)
        feret_diam = regionprops_table(lab, properties=('label', 'feret_diameter_max'))
        return [], feret_diam['feret_diameter_max']

    ext1 = (int(extremes[0][0]), int(extremes[0][1]))
    ext2 = (int(extremes[1][0]), int(extremes[1][1]))

    # these are the two geodesic dist. functions corresponding to the two extreme points
    ext1_geod = geod_dists[endpoint_pixels.index(ext1)]
    ext2_geod = geod_dists[endpoint_pixels.index(ext2)]

    # by summing them, and thresholding with `max_of_prop` we get a path of pixels between the two extremes
    sum_geod = ext1_geod + ext2_geod

    path_pixels = np.argwhere(np.abs(sum_geod - max_of_prop) < 1e-6)[:, ::-1]

    return path_pixels, max_of_prop


GeodesicPathPixels = np.ndarray


def get_longest_geodesic2(region: np.ndarray) -> Tuple[GeodesicPathPixels, float, Tuple[int, int, int, int]]:
    region_ = binary_fill_holes(region)

    rr, cc = np.nonzero(region_ > 0)
    if len(rr) == 0:
        return [], None, (-1, -1, -1, -1)
    top, left = int(np.min(rr)), int(np.min(cc))
    bottom, right = np.max(rr), np.max(cc)

    # get only the region of interest
    region_ = region_[top - 1:bottom + 1, left - 1:right + 1]

    skeleton = skeletonize(region_)

    # find skeleton endpoints with HMT
    endpoint_pixels = find_skeleton_endpoints(skeleton, list(e_codes))
    endpoint_pixels = [(int(endp[0]), int(endp[1])) for endp in endpoint_pixels]

    geod_dists: List[np.ndarray] = []
    prop_function = np.zeros_like(skeleton, dtype=np.float32)

    # for every skeleton endpoint compute geodesic distance transform inside the skeleton
    for i, endpoint in enumerate(endpoint_pixels):
        dist = geodesic_distance_for_skeleton(skeleton, endpoint)
        geod_dists.append(dist)
        # update the propagation function
        prop_function = np.maximum(prop_function, dist)
        # io.imsave(f'/home/radoslav/geo_dist{i}.tiff', dist, check_contrast=False)
    # io.imsave('/home/radoslav/prop_func.tiff', prop_function, check_contrast=False)

    # find the maximum of the propagation function
    max_of_prop = np.max(prop_function)

    # ideally, find at least 2 endpoints that whose furthest pixel is at distance `max_of_prop`. Wont work now on circle-like regions
    extremes = np.argwhere(np.abs(prop_function - max_of_prop) < 1e-6)[:, ::-1]

    if extremes.shape[0] < 2 or len(endpoint_pixels) < 2:
        lab = skimage.measure.label(region, connectivity=2)
        feret_diam = regionprops_table(lab, properties=('label', 'feret_diameter_max'))
        return [], feret_diam['feret_diameter_max'], (top-1, bottom, left-1, right)

    ext1 = (int(extremes[0][0]), int(extremes[0][1]))
    ext2 = (int(extremes[1][0]), int(extremes[1][1]))

    # these are the two geodesic dist. functions corresponding to the two extreme points
    ext1_geod = geod_dists[endpoint_pixels.index(ext1)]
    ext2_geod = geod_dists[endpoint_pixels.index(ext2)]

    # by summing them, and thresholding with `max_of_prop` we get a path of pixels between the two extremes
    sum_geod = ext1_geod + ext2_geod

    path_pixels = np.argwhere(np.abs(sum_geod - max_of_prop) < 1e-6)[:, ::-1]

    return path_pixels, max_of_prop, (top-1, bottom, left-1, right)


def get_node_with_longest_shortest_path(shortest_lengths: typing.Dict[typing.Tuple[int, int], float]) -> typing.Tuple[int, int]:
    return max(shortest_lengths.items(), key=lambda t: t[1])[0]


def compute_longest_geodesic_perf(region: np.ndarray) -> float:
    G = get_graph(region)

    yy, xx = np.nonzero(region)

    if len(yy) == 0:
        return -1.0

    min_idx = np.argmin(xx)
    out_pixel = (yy[min_idx], xx[min_idx])
    out_pixel = (xx[min_idx], yy[min_idx])

    shortest_lengths = networkx.shortest_path_length(G, source=out_pixel, weight='weight')
    dst_pix = get_node_with_longest_shortest_path(shortest_lengths)

    shortest_lengths2 = networkx.shortest_path_length(G, source=dst_pix, weight='weight')
    dst_pix2 = get_node_with_longest_shortest_path(shortest_lengths2)

    shortest_lengths3 = networkx.shortest_path_length(G, source=dst_pix2, weight='weight')
    dst_pix3 = get_node_with_longest_shortest_path(shortest_lengths3)

    return shortest_lengths3[dst_pix3]


def compute_longest_geodesic(region: np.ndarray) -> Tuple[float, Tuple[int, int], Tuple[int, int]]:
    # path = Path('C:\\Users\\radoslav\\Desktop\\')
    # bbox = cv2.boundingRect(region.astype(np.uint8))
    _region = region  #region[bbox[1]:bbox[1]+bbox[3], bbox[0]:bbox[0]+bbox[2]]

    yy, xx = np.nonzero(_region)

    if len(yy) == 0:
        return -1.0, (0, 0), (0, 0)

    min_idx = np.argmin(xx)
    out_pixel = (yy[min_idx], xx[min_idx])

    gdist1 = geodesic_distance_for_skeleton(_region, out_pixel[::-1])

    dst_pix = np.unravel_index(np.argmax(gdist1), gdist1.shape)

    gdist2 = geodesic_distance_for_skeleton(_region, dst_pix[::-1])

    dst_pix2 = np.unravel_index(np.argmax(gdist2), gdist2.shape)

    gdist3 = geodesic_distance_for_skeleton(_region, dst_pix2[::-1])

    dst_pix3 = np.unravel_index(np.argmax(gdist3), gdist3.shape)

    # prop_func = gdist2 + gdist3
    #
    # prop_max = np.max(prop_func)
    #
    # path_pixels = np.nonzero(np.abs(prop_func - prop_max) < 1e-4)
    #

    # path_pixels = find_shortest_path(_region, dst_pix2[::-1], dst_pix3[::-1])
    # path_pixels = ([px[1] for px in path_pixels], [px[0] for px in path_pixels])

    # bgr_region = cv2.cvtColor(255 * _region.astype(np.uint8), cv2.COLOR_GRAY2BGR)
    #
    # bgr_region[path_pixels[0], path_pixels[1]] = [0, 255, 255]
    # bgr_region[out_pixel[0], out_pixel[1]] = [0, 255, 0]
    # bgr_region[dst_pix[0], dst_pix[1]] = [255, 0, 0]
    # bgr_region[dst_pix2[0], dst_pix2[1]] = [0, 0, 255]
    # bgr_region[dst_pix3[0], dst_pix3[1]] = [255, 0, 255]
    #
    # cv2.imwrite(str(path / 'region.png'), 255 * _region.astype(np.uint8))
    # cv2.imwrite(str(path / 'out_pixel.png'), bgr_region)
    # cv2.imshow('bgr_', bgr_region)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()

    return np.max(gdist3), dst_pix2[::-1], dst_pix3[::-1]
