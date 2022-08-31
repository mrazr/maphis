import numpy as np
# import matplotlib.pyplot as plt
import copy
from scipy.signal import find_peaks
from scipy.optimize import linear_sum_assignment


class Profile:
    def __init__(self, values, x=None):
        if x:
            self.x = x
        else:
            self.x = list(range(len(values)))

        self.y = values

    def move_point_x(self, old_idx, new_x, start_idx=0, end_idx=-1):
        if end_idx < 0:
            end_idx += len(self.x)

        start_x = self.x[start_idx]
        end_x = self.x[end_idx]

        assert start_idx < old_idx < end_idx  # only inner points can be moved
        assert start_x < new_x < end_x  # and only within profile's x limits

        old_x = self.x[old_idx]
        for idx in range(start_idx + 1, old_idx):
            self.x[idx] = (new_x - start_x) / (old_x - start_x) * (self.x[idx] - start_x) + start_x

        for idx in range(old_idx, end_idx):
            self.x[idx] = (new_x - end_x) / (old_x - end_x) * (self.x[idx] - end_x) + end_x

    def get_y(self, x, pad_value=0, epsilon=0.0001):
        if x > self.x[-1] or x < self.x[0]:
            return pad_value

        for right_id, right_x in enumerate(self.x):
            if abs(right_x - x) < epsilon:
                return self.y[right_id]

            if right_x > x:
                left_x = self.x[right_id - 1]
                left_y = self.y[right_id - 1]
                right_y = self.y[right_id]
                return (right_y - left_y)*(x - left_x)/(right_x - left_x) + left_y

        return pad_value

    def range_ids(self, min_x, max_x):
        result = []
        for idx, xx in enumerate(self.x):
            if min_x <= xx <= max_x:
                result.append(idx)
        return result

    def plot(self):
        # plt.plot(self.x, self.y)
        pass


def derivative_penalty(model: Profile, reference: Profile) -> int:
    # x-points shared by both profiles
    both_x = set(model.x)
    both_x.union(set(reference.x))
    both_x = sorted(list(both_x))

    # y-points of both profiles
    segments = [(x, model.get_y(x), reference.get_y(x)) for x in both_x]

    # penalize area differences segment by segment
    penalty = 0
    for left_segment, right_segment in zip(segments[:-1], segments[1:]):
        x_left, y_left_model, y_left_reference = left_segment
        x_right, y_right_model, y_right_reference = right_segment
        model_slope = y_right_model - y_left_model
        reference_slope = y_right_reference - y_left_reference
        penalty += abs(model_slope - reference_slope) * (x_right - x_left)

    return penalty


def valid_matching(matched_pairs):
    if not matched_pairs:
        return True

    prev_pair = matched_pairs[0]
    for cur_pair in matched_pairs[1:]:
        if prev_pair[0] > cur_pair[0] or prev_pair[1] > cur_pair[1]:
            return False
    return True


def merge_profiles(model, reference, x_weight=0.5, y_weight=0.5, show_matches=False, fig_name=None):
    """
    Register the given profiles and merge them into one with their relative influence given by weights.
    :param model: model profile
    :param reference: reference profile
    :param x_weight: number in range 0-1 (0 => x-coordinates moved to reference, 1 => x-coordinates moved to model)
    :param y_weight: number in range 0-1 (0 => y-values taken from reference, 1 => y-values taken from model)
    :param show_matches: if True the function shows found matches as a plot
    :param fig_name: filename for saving plots
    :return: merged profile
    """
    assert len(model) == len(reference)
    if fig_name:
        show_matches = True

    model_profile = Profile(model)
    reference_profile = Profile(reference)

    # 1. match minima between end points
    model_minima_pos, _ = find_peaks(-np.array(model))
    reference_minima_pos, _ = find_peaks(-np.array(reference))

    max_cost = derivative_penalty(model_profile, reference_profile)
    matrix_size = len(model_minima_pos) + len(reference_minima_pos)
    cost_matrix = np.full((matrix_size, matrix_size), max_cost)

    for m_id, model_min_pos in enumerate(model_minima_pos):
        for r_id, reference_min_pos in enumerate(reference_minima_pos):
            m = copy.deepcopy(model_profile)
            r = copy.deepcopy(reference_profile)
            new_x = (m.x[model_min_pos] + r.x[reference_min_pos]) / 2.0
            m.move_point_x(model_min_pos, new_x)
            r.move_point_x(reference_min_pos, new_x)
            cost_matrix[m_id, r_id] = derivative_penalty(m, r)

    mi_ind, ri_ind = linear_sum_assignment(cost_matrix)
    # print(cost_matrix)
    matched_ids = [(m_id, r_id) for m_id, r_id in zip(mi_ind, ri_ind)
                   if m_id < len(model_minima_pos) and r_id < len(reference_minima_pos)]
    # print(matched_ids)
    if not valid_matching(matched_ids):
        print("Matching is invalid. Matching result is ignored!", matched_ids)
        matched_ids = []

    # 1. align profiles
    orig_x = copy.deepcopy(model_profile.x)
    model_start_idx = 3
    reference_start_idx = 3
    for m_id, r_id in matched_ids:
        new_x = x_weight*model_minima_pos[m_id] + (1 - x_weight)*reference_minima_pos[r_id]
        # print("Register model:", m_id, new_x, model_start_idx)
        model_profile.move_point_x(model_minima_pos[m_id], new_x, start_idx=model_start_idx, end_idx=-3)
        # print("Register reference:", r_id, new_x, reference_start_idx)
        reference_profile.move_point_x(reference_minima_pos[r_id], new_x, start_idx=reference_start_idx, end_idx=-3)
        model_start_idx = model_minima_pos[m_id]
        reference_start_idx = reference_minima_pos[r_id]

    # if show_matches:
    #     ax = plt.subplot(211)
    #     plt.plot(model, 'r')
    #     plt.plot(reference, 'b')
    #     ax.set_xticks([])
    #     ax.set_yticks([])
    #     plt.xlabel('Matched extrema', fontsize=12)
    #     for m_id, r_id in matched_ids:
    #         plt.plot([model_minima_pos[m_id], reference_minima_pos[r_id]],
    #                  [model[model_minima_pos[m_id]], reference[reference_minima_pos[r_id]]], 'k-', linewidth=3)
    #     # print("MODEL:", model)
    #     #print("minima_pos", model_minima_pos)
    #     plt.plot(model_minima_pos, model[model_minima_pos], 'ro')
    #     plt.plot(reference_minima_pos, reference[reference_minima_pos], 'bo')
    #     # plt.ylim(0, 0.05)
    #
    #     ax = plt.subplot(212)
    #     ax.set_xticks([])
    #     ax.set_yticks([])
    #     plt.xlabel('Aligned profiles', fontsize=12)
    #     plt.plot(model_profile.x, model_profile.y, 'r')
    #     plt.plot(reference_profile.x, reference_profile.y, 'b')
    #     plt.ylim(0, 0.05)

    # 2. resample the profiles and average them
    average_y = np.array([y_weight*model_profile.get_y(x) + (1 - y_weight)*reference_profile.get_y(x) for x in orig_x])
    # print("Model:    ", model)
    # print("Reference:", reference)
    # print("Average:  ", average_y)
    # if show_matches:
    #     plt.plot(orig_x, average_y, 'k--', linewidth=2)
    #     if fig_name:
    #         plt.savefig(fig_name)
    #     plt.close()
    #     # plt.show()

    return average_y


def get_median_profile(profiles, show_fig=False, fig_name=None):
    """
    Create a median profile from given profiles
    :param profiles: 2D numpy array, where the individual profiles are rows
    :param show_fig: indicates whether to show figure or not
    :param fig_name: optional name of output file for saving plots
    :return: Median profile (1D numpy array) obtained after registration of the input profiles
    """
    if fig_name:
        show_fig = True

    # if show_fig:
    #     ax = plt.subplot(211)
    #     plt.plot(profiles.T)
    #     ax.set_xticks([])
    #     ax.set_yticks([])
    #     plt.xlabel('Median profile (--) of raw misaligned profiles', fontsize=12)

    # Sort the profiles by mean similarity to other profiles
    similarities = [np.mean([derivative_penalty(Profile(model), Profile(reference))
                             for model in profiles]) for reference in profiles]
    order = np.argsort(similarities)

    # Select the most similar profile as a reference
    reference_profile = profiles[order[0]]
    # mean_profile = profiles[order[0]]
    #
    # for pid in range(1, len(profiles)):
    #     weight = pid/(pid + 1)
    #     mean_profile = merge_profiles(mean_profile, profiles[order[pid]], x_weight=weight, y_weight=weight)
    # plt.plot(mean_profile, 'r--', linewidth=2)
    #
    # reference_profile = mean_profile
    # if show_fig:
    #     plt.plot(np.mean(profiles, axis=0), 'k--', linewidth=2)

    # Register all profiles to the mean profile
    registered_profiles = np.empty_like(profiles)

    for pid in range(len(profiles)):
        registered_profiles[pid] = merge_profiles(reference_profile, profiles[pid], x_weight=1, y_weight=0)

    median_profile = np.median(registered_profiles, axis=0)


    # if show_fig:
    #     ax = plt.subplot(212)
    #     ax.set_xticks([])
    #     ax.set_yticks([])
    #     plt.xlabel('Median profile (--) of aligned profiles', fontsize=12)
    #     plt.plot(registered_profiles.T)
    #     plt.plot(median_profile, 'k--', linewidth=2)
    #
    #     if fig_name:
    #         plt.savefig(fig_name)
    #         plt.close()
    #     else:
    #         plt.show()

    return median_profile


# An example how to use get_median_profile function
# def test_median_profiles():
#     profiles = ProfileTable('bodyprofiles.csv')
#
#     codes = profiles.get_codes()
#     # codes = codes[0:1]
#     for code in codes:
#         selection = profiles.get_profiles(code)
#         get_median_profile(selection, fig_name=code + '.png')
#

# An example code for comparing two profiles (e.g., mimic vs. model) using merge_profiles function
#
# def save_model_vs_mimic(pair_number):
#     profiles = ProfileTable('bodyprofiles.csv')
#
#     mimic_profile = get_median_profile(profiles.get_profiles('mimic' + str(pair_number)))
#     model_profile = get_median_profile(profiles.get_profiles('model' + str(pair_number)))
#
#     merge_profiles(mimic_profile, model_profile, fig_name='matching_model_mimic_' + str(pair_number) + '.png')
#
#     reg_mimic_profile = merge_profiles(mimic_profile, model_profile, y_weight=1)
#     reg_model_profile = merge_profiles(mimic_profile, model_profile, y_weight=0)
#
#     ax = plt.subplot(211)
#     plt.plot(mimic_profile, 'r')
#     plt.plot(model_profile, 'b')
#     ax.set_xticks([])
#     ax.set_yticks([])
#     plt.xlabel('Model and mimic unaligned', fontsize=12)
#
#     ax = plt.subplot(212)
#     plt.plot(reg_mimic_profile, 'r')
#     plt.plot(reg_model_profile, 'b')
#     ax.set_xticks([])
#     ax.set_yticks([])
#     plt.xlabel('Model and mimic aligned', fontsize=12)
#
#     # plt.show()
#     plt.savefig('model_mimic_' + str(pair_number) + '.png')
#     plt.close()
#
#

