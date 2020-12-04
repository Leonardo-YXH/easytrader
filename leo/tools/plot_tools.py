# -*- coding:utf-8 -*-
"""
@author: leonardo
@created time: 2020-07-01
@last modified time:2020-07-01
"""

import matplotlib.pyplot as plt
from matplotlib import cm, colors
from matplotlib.ticker import LinearLocator, FormatStrFormatter
from mpl_toolkits.mplot3d import axes3d
import numpy as np
from mpl_toolkits.axisartist.parasite_axes import HostAxes, ParasiteAxes


def plot_surface(x, y, z):
    fig = plt.figure()
    ax = fig.gca(projection='3d')
    surf = ax.plot_surface(x, y, z, cmap=cm.coolwarm, linewidth=0, antialiased=False)
    # ax.set_zlim(-1.01, 1.01)
    ax.zaxis.set_major_locator(LinearLocator(10))
    ax.zaxis.set_major_formatter(FormatStrFormatter('%.02f'))
    fig.colorbar(surf, shrink=0.5, aspect=5)
    plt.show()


def plot_surface2(x, y, z):
    ax = plt.axes(projection='3d')
    ax.plot_surface(x, y, z, rstride=1, cstride=1, cmap='viridis', edgecolor='none')
    plt.show()


def plot_multi_y(line_series_list, line_label_list, scatter_series_list, scatter_label_list):
    """
    第一条line做主轴,散点与主轴共用Y轴
    :param line_series_list:
    :param line_label_list:
    :param scatter_series_list:
    :param scatter_label_list:
    :return:
    """
    color_list = ['red', 'green', 'blue', 'yellow', 'pink', 'black', 'orange']
    fig = plt.figure(1)
    host_axes = HostAxes(fig, [0.1, 0.1, 0.6, 0.8])
    fig.add_axes(host_axes)
    host_axes.set_ylabel(line_label_list[0])
    host_axes.axis['right'].set_visible(False)
    host_axes.set_ylim(min(line_series_list[0][1]) * 0.9, max(line_series_list[0][1]) * 1.1)
    host_axes.plot(line_series_list[0][0], line_series_list[0][1], label=line_label_list[0],
                   color=color_list[0])

    label_offset = 0
    # line_axes = []
    for i in range(len(line_series_list) - 1):
        axes = ParasiteAxes(host_axes, sharex=host_axes)
        axes.set_ylabel(line_label_list[i + 1])
        axis_line = axes.get_grid_helper().new_fixed_axis

        axes.axis['right' + str(label_offset)] = axis_line(loc='right', axes=axes, offset=(label_offset, 0))
        axes.axis['right' + str(label_offset)].label.set_color(color_list[i + 1])
        axes.axis['right' + str(label_offset)].major_ticks.set_color(color_list[i + 1])
        axes.axis['right' + str(label_offset)].major_ticklabels.set_color(color_list[i + 1])
        axes.axis['right' + str(label_offset)].line.set_color(color_list[i + 1])
        label_offset += 40

        axes.set_ylim(min(line_series_list[i + 1][1]) * 0.9, max(line_series_list[i + 1][1]) * 1.1)

        axes.plot(line_series_list[i + 1][0], line_series_list[i + 1][1], label=line_label_list[i + 1],
                  color=color_list[i + 1])

        # line_axes.append(axes)
        host_axes.parasites.append(axes)

    # scatter_axes = []
    for i in range(len(scatter_series_list)):  # 与主轴共用Y轴
        # axes = ParasiteAxes(host_axes, sharex=host_axes)
        # axes.set_ylabel(scatter_label_list[i])
        # axis_line = axes.get_grid_helper().new_fixed_axis

        # axes.axis['right' + str(label_offset)] = axis_line(loc='right', axes=axes, offset=(label_offset, 0))
        color_item = color_list[len(line_label_list) + i + 1]
        # axes.axis['right' + str(label_offset)].label.set_color(color_item)
        # axes.axis['right' + str(label_offset)].major_ticks.set_color(color_item)
        # axes.axis['right' + str(label_offset)].major_ticklabels.set_color(color_item)
        # axes.axis['right' + str(label_offset)].line.set_color(color_item)
        # label_offset += 40

        # axes.set_ylim(min(scatter_series_list[i][1]), max(scatter_series_list[i][1]))

        host_axes.scatter(scatter_series_list[i][0], scatter_series_list[i][1], label=scatter_label_list[i],
                          color=color_item)
        # scatter_axes.append(axes)
        # host_axes.parasites.append(axes)

    host_axes.legend()
    plt.show()


if __name__ == '__main__':
    import math

    y_size = 30
    x = np.arange(0, y_size, 1)
    line_size = 4
    line_series_list = []
    line_label_list = []
    for i in range(line_size):
        y = np.random.random(y_size) * math.pow(10, i)
        line_series_list.append([x, y])
        line_label_list.append('line{}'.format(i))
    scatter_series_list = []
    s_x = [2, 6]
    scatter_series_list.append([s_x, line_series_list[0][1][s_x]])
    s_x = [4, 8]
    scatter_series_list.append([s_x, line_series_list[0][1][s_x]])
    plot_multi_y(line_series_list, line_label_list, scatter_series_list, ['scatter1', 'scatter2'])
