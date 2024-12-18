import math
import os
import sys
from argparse import RawTextHelpFormatter
from datetime import datetime as dt
from datetime import timedelta as td
from io import StringIO
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from gooey import Gooey, GooeyParser
from matplotlib import animation


def anim_progress(cur_frame, total_frames):
    percent = "{0:.2f}".format(cur_frame * 100 / total_frames).zfill(5)
    print(
        "Saving frame {0} out of {1} : {2}%".format(
            str(cur_frame), str(total_frames), percent
        )
    )
    sys.stdout.flush()


def animate(plots, length, interval, args):
    for plts in plots.keys():

        def anim(i):
            if "line" in plots[plts]:
                x_left = None
                x_right = None
                if i <= 120:
                    x_left = -plots[plts]["line"].get_xdata()[120 - i]
                    x_right = plots[plts]["line"].get_xdata()[i]
                elif i + 120 >= length:
                    x_left = plots[plts]["line"].get_xdata()[i - 120]
                    x_right = plots[plts]["line"].get_xdata()[i] + interval / 1000
                else:
                    x_left = plots[plts]["line"].get_xdata()[i - 120]
                    x_right = plots[plts]["line"].get_xdata()[i]
                plots[plts]["ax"].set_xlim(
                    x_left,
                    x_right,
                )
                return (plots[plts]["line"],)
            else:
                x_left = None
                x_right = None
                if i <= 120:
                    x_left = -plots[plts]["line1"].get_xdata()[120 - i]
                    x_right = plots[plts]["line1"].get_xdata()[i]
                elif i + 120 >= length:
                    x_left = plots[plts]["line1"].get_xdata()[i - 120]
                    x_right = plots[plts]["line1"].get_xdata()[i] + interval / 1000
                else:
                    x_left = plots[plts]["line1"].get_xdata()[i - 120]
                    x_right = plots[plts]["line1"].get_xdata()[i]
                plots[plts]["ax"].set_xlim(
                    x_left,
                    x_right,
                )
                plots[plts]["ax2"].set_xlim(
                    x_left,
                    x_right,
                )
                return (
                    plots[plts]["line1"],
                    plots[plts]["line2"],
                )

        anim_func = animation.FuncAnimation(
            plots[plts]["figure"],
            anim,
            frames=length,
            interval=interval,
            blit=True,
            save_count=100,
        )

        if (
            (plts == "FPS" and args.Export_FPS)
            or (plts == "Frametime" and args.Export_Frametime)
            or (plts == "Combined" and args.Export_Combined)
        ):
            print("Saving {0} Graph to {1}".format(plts, plots[plts]["filename"]))
            anim_func.save(
                plots[plts]["filename"],
                fps=60,
                dpi=args.DPI,
                savefig_kwargs={"transparent": True, "facecolor": "None"},
                progress_callback=anim_progress,
            )
            anim_progress(length, length)
            print("\nDone.\n")


def main(args):
    my_file = open(args.CSV_Report, "r")
    data = my_file.read()

    # We'll attempt to use a semi-colon as a separator, and look for columns titled TIMESTAMP and FRAMERATE
    try:
        df = pd.read_csv(
            StringIO(data),
            sep=";",
            usecols=lambda x: x.upper() in ["TIMESTAMP", "FRAMERATE"],
            index_col=0,
        )
    except Exception:
        raise ValueError("No valid column header values found.")

    length_original = len(df.index)  # Total count of frames before interpolation

    index_fixed = []
    for i in df.index:
        index_fixed.append(i.replace("_", " ").replace("-", " ").replace(":", " "))
    for i in range(len(index_fixed)):
        i_split = index_fixed[i].split(" ")
        i_dt = dt(
            year=int(i_split[0]),
            month=int(i_split[1]),
            day=int(i_split[2]),
            hour=int(i_split[3]),
            minute=int(i_split[4]),
            second=int(i_split[5]),
            microsecond=int(i_split[6]) * 1000,
        )
        if i == 0:
            index_fixed[i] = i_dt
        else:
            index_fixed[i] = i_dt - index_fixed[0]
    index_fixed[0] = td(
        days=0, seconds=0, microseconds=0, milliseconds=0, minutes=0, hours=0, weeks=0
    )
    df.index = pd.TimedeltaIndex(index_fixed)

    df = df.resample("16.67L").nearest()

    index_scaled = []
    df.index = df.index.to_pytimedelta()
    for i in range(len(df.index)):
        index_scaled.append(df.index[i].total_seconds())
    df.index = index_scaled

    df.to_csv("df.csv")

    # the index is really the values actually the FPS_timestamp column.
    # x -> FPS timestamps
    # y -> FPS value at that timestamp
    x = pd.Series(df.index)
    y = pd.Series(df["framerate"])

    # set the all the plot params
    plt.rcParams.update(
        {
            "figure.facecolor": (0.0, 0.0, 0.0, 0.0),
            "figure.edgecolor": "black",
            "axes.facecolor": (0.0, 0.0, 0.0, 0.0),
            "savefig.facecolor": (0.0, 0.0, 0.0, 0.0),
            "legend.facecolor": (0.0, 0.0, 0.0, 0.0),
            "legend.edgecolor": "black",
            "legend.frameon": False,
            "savefig.transparent": True,
            "animation.codec": "hevc_qsv",
            "font.size": 26,
        }
    )

    plotters = dict()
    if args.Export_FPS:
        plotters["FPS"] = {"figure": plt.figure(1, animated=True)}
    if args.Export_Frametime:
        plotters["Frametime"] = {"figure": plt.figure(2, animated=True)}
    if args.Export_Combined:
        plotters["Combined"] = {"figure": plt.figure(3, animated=True)}

    for key, plts in plotters.items():
        plts["figure"].patch.set_alpha(0.0)
        # The inch size actually gets tranlated into the resolution
        # So 19.2 x 10.8 -> 1920x1080
        if args.Resolution:
            if args.Resolution == "720p":
                plts["figure"].set_size_inches(12.8, 7.2)
            elif args.Resolution == "1080p":
                plts["figure"].set_size_inches(19.2, 10.8)
            elif args.Resolution == "1440p":
                plts["figure"].set_size_inches(25.6, 14.4)
            elif args.Resolution == "4k":
                plts["figure"].set_size_inches(38.4, 21.6)
        else:
            plts["figure"].set_size_inches(19.2, 10.8)

        if args.DPI:
            plts["figure"].dpi = args.DPI
        else:
            plts["figure"].dpi = 100

        plts["ax"] = plts["figure"].subplots()

    # Some FPS values can be 0
    # Frame times are calculated as 1000 / FPS value
    # That means we'd get a division-by-zero error
    # To get around this, we ignore any division-by zero errors
    # The next problem is that the program will put in "inf" and "-inf" as the
    # values, so we have to replace them with 0 so the graph doesn't freak out
    print("Removing inf frame-time values from doing division-by-zero.")
    with np.errstate(divide="ignore", invalid="ignore"):
        y2 = pd.Series(1000 / df["framerate"])
    y2[y2 == np.inf] = np.nan
    y2[y2 == -np.inf] = np.nan

    y = y.interpolate(method="cubic")
    y2 = y2.interpolate(method="cubic")

    length = len(x)  # Total count of frames
    fps_min = y.min()  # Lowest recorded FPS value
    fps_max = y.max()  # Highest recorded FPS value
    fps_mean = y.mean()  # Average FPS
    fps_median = y.median()  # Median FPS
    if "FPS" in plotters.keys():
        plotters["FPS"]["Minimum"] = fps_min
        plotters["FPS"]["Maximum"] = fps_max
        plotters["FPS"]["Mean"] = fps_mean
        plotters["FPS"]["Median"] = fps_median

    frametime_min = y2.min()  # Lowest recorded frametime
    frametime_max = y2.max()  # Highest recorded frametime
    frametime_mean = y2.mean()  # Average frametime
    frametime_median = y2.median()  # Median frametime
    if "Frametime" in plotters.keys():
        plotters["Frametime"]["Minimum"] = frametime_min
        plotters["Frametime"]["Maximum"] = frametime_max
        plotters["Frametime"]["Mean"] = frametime_mean
        plotters["Frametime"]["Median"] = frametime_median

    # This actually plays the animations for each chart we want
    # The program doesn't display the graphs live,
    # the animations are generated in the background.
    fps_interval = float(100 / 6)

    for key, plts in plotters.items():
        # Set the range for the initial X-axis
        plts["ax"].set_xlim(x[0], x[120])
        # Remove the X-axis ticks
        plts["ax"].set_xticklabels([])

    # Now we save each individual graph as it's own file.
    # We choose which files are saved based on the user's input in the
    # beginning of the program.

    rem = os.path.basename(args.CSV_Report)
    my_path, my_file = os.path.abspath(args.CSV_Report).split(rem)
    if my_path == "":
        my_path, my_file = os.getcwd().split("fps_2_chart.py")

    if args.Export_FPS:
        plotters["FPS"]["ax"].set_ylim(0, fps_max * 1.1)
        if args.Yaxis_Label:
            plotters["FPS"]["ax"].set_ylabel("FPS", color="b",fontname="Microsoft YaHei",fontsize=28)
        plotters["FPS"]["filename"] = "{0}_fps.mov".format(args.Output)
        line_fps = mpl.lines.Line2D(x, y, color="b", antialiased=True)
        line_fps.set_animated(True)
        plotters["FPS"]["line"] = plotters["FPS"]["ax"].add_line(line_fps)
    if args.Export_Frametime:
        plotters["Frametime"]["ax"].set_ylim(0, frametime_max * 1.1)
        if args.Yaxis_Label:
            plotters["FPS"]["ax"].set_ylabel("帧时间（毫秒）", color="b",fontname="Microsoft YaHei",fontsize=28)
        plotters["Frametime"]["filename"] = "{0}_frametime.mov".format(args.Output)
        line_frametime = mpl.lines.Line2D(x, y2, color="r", antialiased=True)
        line_frametime.set_animated(True)
        plotters["Frametime"]["line"] = plotters["Frametime"]["ax"].add_line(
            line_frametime
        )
    if args.Export_Combined:
        plotters["Combined"]["ax"].set_ylim(0, fps_max * 1.1)
        if args.Yaxis_Label:
            plotters["Combined"]["ax"].set_ylabel("FPS", color="b",fontname="Microsoft YaHei",fontsize=28)

        plotters["Combined"]["filename"] = "{0}_combined.mov".format(args.Output)

        line_combined1 = mpl.lines.Line2D(x, y, color="b", antialiased=True)
        plotters["Combined"]["line1"] = plotters["Combined"]["ax"].add_line(
            line_combined1
        )
        plotters["Combined"]["ax2"] = plotters["Combined"]["ax"].twinx()
        plotters["Combined"]["ax2"].set_yticks(
            [tick for tick in range(0, math.ceil(y2.max()), math.ceil(y2.max() / 10))]
        )

        plotters["Combined"]["figure"].add_axes(
            plotters["Combined"]["ax2"], animated=True
        )
        plotters["Combined"]["ax2"].set_ylabel("帧时间（毫秒）", color="r",fontname="Microsoft YaHei",fontsize=28)
        line_combined2 = mpl.lines.Line2D(x, y2, color="r", antialiased=True)
        plotters["Combined"]["line2"] = plotters["Combined"]["ax"].add_line(
            line_combined2
        )

    animate(plotters, length, fps_interval, args)
    print("# of original data points: {0}".format(length_original))
    print("# of Frames: {0}".format(length))
    print("Minimum FPS: {0}".format(fps_min))
    print("Maximum FPS: {0}".format(fps_max))
    print("Mean FPS: {0}".format(fps_mean))
    print("Median FPS: {0}".format(fps_median))
    print("Minimum Frametime: {0}ms".format(frametime_min))
    print("Maximum Frametime: {0}ms".format(frametime_max))
    print("Mean Frametime: {0}ms".format(frametime_mean))
    print("Median Frametime: {0}ms".format(frametime_median))


@Gooey(
    program_name="帧率图表生成器",
    default_size=(1280, 720),
    optional_cols=3,
    advanced=True,
    navigation="TABBED",
    clear_before_run=True,
    menu=[
        {
            "name": "帧率图表生成器",
            "items": [{
                "type": "AboutDialog",
                "menuTitle": "关于",
                "description": "创建记录FPS值的实时视频图表\n汉化：吊打小逗比",
                "version": "0.8-CN",
                "copyright": "2020",
                "website": "https://github.com/DDXDB/FPS_Graph_Maker-CN",
                "license": "GPLv3",
            }],
        },
    ],
)
def parse_arguments():
    """Parse input arguments."""

    main_help = "Plot CSV report to to a live video graph."
    parser = GooeyParser(description=main_help, formatter_class=RawTextHelpFormatter)
    parser.add_argument(
        "CSV_Report",
        widget="FileChooser",
        gooey_options={
            "default_dir": str(Path(__file__).parent),
            "message": "Input file name",
            "initial_value": "CSV Report",
            "wildcard": "Comma separated file (*.csv)|*.csv|" "All files (*.*)|*.*",
        },
        help="CSV报告文件.",
    )

    output_help = '输出文件名 (默认: "graph").\n'
    output_help += '根据您生成的内容，输出将附加"_fps"或"_frametime"或"_both"在后面\n'
    output_help += '(示例: "graph"将输出"graph_fps.mov").'
    parser.add_argument(
        "Output",
        default="graph",
        widget="FileSaver",
        gooey_options={
            "default_dir": str(Path(__file__).parent),
            "message": "Output file name",
            "default_file": "graph",
            "initial_value": "graph",
        },
        help=output_help,
    )

    export_group = parser.add_argument_group(
        "导出选项", "选择要导出的文件。"
    )
    Export_FPS_help = (
        "如果想要生成和导出FPS图表，请勾选此框。\n"
    )
    export_group.add_argument(
        "--fps",
        dest="Export_FPS",
        action="store_true",
        help=Export_FPS_help,
    )

    Export_Frametime_help = (
        "如果要生成并导出Frametime图表，请选中此框。\n"
    )
    export_group.add_argument(
        "--frametime",
        dest="Export_Frametime",
        action="store_true",
        help=Export_Frametime_help,
    )

    Export_Combined_help = "如果你想生成并导出FPS + Frametime的组合图表，请勾选此框。\n"
    export_group.add_argument(
        "--combined",
        dest="Export_Combined",
        action="store_true",
        help=Export_Combined_help,
    )

    quality_group = parser.add_argument_group(
        "质量选项",
        "选择导出图表文件的分辨率和DPI以及编码格式。",
    )
    res_help = "选择图表视频的分辨率（默认: 1080p）。\n"
    res_help += "请注意，数值越高意味着文件越大，编码时间也就越长。"
    quality_group.add_argument(
        "-r",
        "--resolution",
        type=str,
        dest="Resolution",
        default="1080p",
        choices=["720p", "1080p", "1440p", "4k"],
        widget="Dropdown",
        gooey_options={
            "initial_value": "1080p",
        },
        help=res_help,
    )
    # quality_group.add_argument(
    #     "-c",
    #     type=str,
    #     dest="codec",
    #     default="qtrle",
    #     choices=['libx264', 'libx265', 'libvpx-vp9', 'h264_nvenc', 'hevc_nvenc', 'h264_amf', 'hevc_amf', 'h264_qsv', 'hevc_qsv', 'h264_videotoolbox', 'hevc_videotoolbox'],
    #     widget="Dropdown",
    #     gooey_options={
    #         "initial_value": "qtrle",
    #     },
    #     help=res_help,
    # )

    dpi_help = "选择图表图像和视频的DPI值（默认: 100）。\n"
    dpi_help = "100意味着与你设置的分辨率相同，而200 DPI将是设置分辨率的2倍。\n"
    dpi_help += "请注意，数值越高意味着文件越大，编码时间也就越长。\n"
    quality_group.add_argument(
        "-d",
        "--dpi",
        type=int,
        dest="DPI",
        default=100,
        widget="Slider",
        gooey_options={
            "min": 2,
            "max": 200,
            "initial_value": 100,
        },
        help=dpi_help,
    )

    graph_group = parser.add_argument_group(
        "图表选项",
        "杂项图表相关选项。",
    )

    yaxis_label_help = "如果希望在导出图表的两侧显示y轴标签，请选中此框。\n"
    graph_group.add_argument(
        "--yaxis-label",
        dest="Yaxis_Label",
        action="store_true",
        help=yaxis_label_help,
    )

    args = parser.parse_args()

    if str(args.CSV_Report) == "CSV报告":
        raise ValueError(
            "CSV报表参数是必需的，但不是用户提供的。"
        )

    if (
        (
            "Export_FPS" not in args
            or ("Export_FPS" in args and args.Export_FPS is False)
        )
        and (
            "Export_Frametime" not in args
            or ("Export_Frametime" in args and args.Export_Frametime is False)
        )
        and (
            "Export_Combined" not in args
            or ("Export_Combined" in args and args.Export_Combined is False)
        )
    ):
        # raise ValueError("Must choose at least one graph type to export.")
        print("No export files chosen - printing general statistics.")

    return args


if __name__ == "__main__":
    args = parse_arguments()
    main(args)
